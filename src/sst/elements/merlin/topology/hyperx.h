// -*- mode: c++ -*-

// Copyright 2009-2021 NTESS. Under the terms
// of Contract DE-NA0003525 with NTESS, the U.S.
// Government retains certain rights in this software.
//
// Copyright (c) 2009-2021, NTESS
// All rights reserved.
//
// Portions are copyright of other developers:
// See the file CONTRIBUTORS.TXT in the top level directory
// the distribution for more information.
//
// This file is part of the SST software package. For license
// information, see the LICENSE file in the top level directory of the
// distribution.


#ifndef COMPONENTS_MERLIN_TOPOLOGY_HYPERX_H
#define COMPONENTS_MERLIN_TOPOLOGY_HYPERX_H

#include <sst/core/event.h>
#include <sst/core/link.h>
#include <sst/core/params.h>
#include <sst/core/rng/sstrng.h>

#include <string.h>
#include <vector>

#include "sst/elements/merlin/router.h"

#include "sst/core/serialization/serializable.h"


namespace SST {
namespace Merlin {


namespace Hyperx {

// Classes to parse the failed link format.  Designed to be used with
// Params::find_array<FailedLink>().
struct FailedLinkIndex : public SST::Core::Serialization::serializable {
    int16_t low_index;
    int16_t high_index;
    int16_t slice;

    void serialize_order(SST::Core::Serialization::serializer &ser) override {
        ser & low_index;
        ser & high_index;
        ser & slice;
    }

    ImplementSerializable(SST::Merlin::Hyperx::FailedLinkIndex)
};

struct FailedLink {
    std::vector<int16_t> base;
    int16_t dimension;
    FailedLinkIndex info;

    // Format for string is index0:index1:index2, where one of the
    // entries will include two indices and a slice: 1-2,0.  You can
    // leave the slice out if there is only one slice in that
    // dimension.

    // Example: 1:2-4,1:3, would mean slice 1 between 1:2:3 and 1:4:3
    // is marked as failed
    FailedLink(const std::string& format)
    {
        // TODO:  Still need to add error checking on the string format
        std::vector<std::string> tokens;
        std::string parse = format + ":";
        int dims = -1;  // first token is slice
        int start = 0;
        int count = 0;
        size_t index = parse.find_first_of(":",start);
        while ( index != std::string::npos ) {
            tokens.push_back(parse.substr(start,index));
            start = index + 1;
            index = parse.find_first_of(":",start);
            dims++;
        }
        info.slice = SST::Core::from_string<int16_t>(tokens[0]);
        tokens.erase(tokens.begin());

        // Process each of the tokens
        int current_dim = 0;
        for ( auto x : tokens ) {
            size_t index = x.find_first_of("-");
            if ( index == std::string::npos ) {
                // Just a normal dimension
                base.push_back(SST::Core::from_string<int16_t>(x));
            }
            else {
                // Dimension with missing link
                base.push_back(-1);
                dimension = current_dim;
                info.low_index = SST::Core::from_string<int16_t>(x.substr(0,index));
                int16_t other_index = SST::Core::from_string<int16_t>(x.substr(index+1));
                if ( other_index < info.low_index ) {
                    info.high_index = info.low_index;
                    info.low_index = other_index;
                }
                else {
                    info.high_index = other_index;
                }
            }
            current_dim++;
        }
    }

    // Generate a location hash.  We need a multiplier to use for each
    // dimension.  For now, we'll just use 64 as that's the max
    // currently supported by the data structures used by the topology
    // object to rack things.

    // This has is used to identify all locations in the network
    // that would be affected by a failed link.  So, all locations
    // that have the same indices for all but the dimension with
    // -1 (the dimension with the failed link) will hash to the
    // same number when leaving that dimension out of the
    // computation.

    // This hash is suitable for using as a key in a map to store the
    // failed link info
    uint64_t getLocationHash()
    {
        uint64_t max_dim_size = 64;
        uint64_t multiplier = 1;
        uint64_t location_hash = 0;
        for ( int i = 0; i < base.size(); ++i ) {
            if ( base[i] != -1 ) {
                location_hash += base[i] * multiplier;
            }
            multiplier *= max_dim_size;
        }
        return location_hash;
    }

    // Gets a compatable hash with the hash generated for a FailedLink
    // object.  The vector is the indices of the location and the
    // blank_dimension input is the dimension to test for failed
    // links.  If not using a map to check for failed links, the
    // isMatch() function can be used to check each FailedLink object
    // individually.
    static uint64_t getLocationHash(std::vector<int16_t> location, int16_t blank_dimension)
    {
        uint64_t max_dim_size = 64;
        uint64_t multiplier = 1;
        uint64_t location_hash = 0;
        for ( int i = 0; i < location.size(); ++i ) {
            if ( i != blank_dimension ) {
                location_hash += location[i] * multiplier;
            }
            multiplier *= max_dim_size;
        }
        return location_hash;
    }

    // This function will return -1 if the passed in location does not
    // match with the location of the failed links. If there is a
    // match, the return value will be the dimension with the failed
    // links.
    // int isMatch(std::vector<int16_t> location) {
    int isMatch(int* location) {
        for ( int i = 0; i < base.size(); ++i ) {
            if ( base[i] == -1 ) continue;
            if ( base[i] != location[i] ) return -1;
        }
        return dimension;
    }
};

} // namespace Hyperx

class topo_hyperx_event : public internal_router_event {
public:
    int dimensions;
    // First non aligned dimension
    int last_routing_dim;
    int* dest_loc;
    bool val_route_dest;
    int* val_loc;

    id_type id;
    bool rerouted;


    topo_hyperx_event() : internal_router_event() {}
    topo_hyperx_event(int dim) :
        internal_router_event(),
        dimensions(dim),
        last_routing_dim(-1),
        val_route_dest(false)
    {
        dest_loc = new int[dim];
        val_loc = new int[dim];
        id = generateUniqueId();
    }
    virtual ~topo_hyperx_event() { delete[] dest_loc; delete[] val_loc; }
    virtual internal_router_event* clone(void) override
    {
        topo_hyperx_event* tte = new topo_hyperx_event(*this);
        tte->dest_loc = new int[dimensions];
        memcpy(tte->dest_loc, dest_loc, dimensions*sizeof(int));
        return tte;
    }

    void getUnalignedDimensions(int* curr_loc, std::vector<int>& dims) {
        for (int i = 0; i < dimensions; ++i ) {
            if ( dest_loc[i] != curr_loc[i] ) dims.push_back(i);
        }
    }

    void serialize_order(SST::Core::Serialization::serializer &ser)  override {
        internal_router_event::serialize_order(ser);
        ser & dimensions;
        ser & last_routing_dim;

        if ( ser.mode() == SST::Core::Serialization::serializer::UNPACK ) {
            dest_loc = new int[dimensions];
        }

        for ( int i = 0 ; i < dimensions ; i++ ) {
            ser & dest_loc[i];
        }

        if ( ser.mode() == SST::Core::Serialization::serializer::UNPACK ) {
            val_loc = new int[dimensions];
        }

        for ( int i = 0 ; i < dimensions ; i++ ) {
            ser & val_loc[i];
        }

        ser & val_route_dest;
        ser & id;
        ser & rerouted;
    }

protected:

private:
    ImplementSerializable(SST::Merlin::topo_hyperx_event)

};


class topo_hyperx_init_event : public topo_hyperx_event {
public:
    int phase;

    topo_hyperx_init_event() : topo_hyperx_event() {}
    topo_hyperx_init_event(int dim) : topo_hyperx_event(dim), phase(0) { }
    virtual ~topo_hyperx_init_event() { }
    virtual internal_router_event* clone(void) override
    {
        topo_hyperx_init_event* tte = new topo_hyperx_init_event(*this);
        tte->dest_loc = new int[dimensions];
        tte->val_loc = new int[dimensions];
        memcpy(tte->dest_loc, dest_loc, dimensions*sizeof(int));
        return tte;
    }

    void serialize_order(SST::Core::Serialization::serializer &ser)  override {
        topo_hyperx_event::serialize_order(ser);
        ser & phase;
    }

private:
    ImplementSerializable(SST::Merlin::topo_hyperx_init_event)

};


class RNGFunc {
    RNG::SSTRandom* rng;

public:
    RNGFunc(RNG::SSTRandom* rng) : rng(rng) {}

    int operator() (int i) {
        return rng->generateNextUInt32() % i;
    }
};

class topo_hyperx: public Topology {

public:

    SST_ELI_REGISTER_SUBCOMPONENT_DERIVED(
        topo_hyperx,
        "merlin",
        "hyperx",
        SST_ELI_ELEMENT_VERSION(0,1,0),
        "Multi-dimensional hyperx topology object",
        SST::Merlin::Topology)

    SST_ELI_DOCUMENT_PARAMS(
        {"hyperx:shape",        "Shape of the mesh specified as the number of routers in each dimension, where each dimension is separated by a colon.  For example, 4x4x2x2.  Any number of dimensions is supported."},
        {"hyperx:width",        "Number of links between routers in each dimension, specified in same manner as for shape.  For example, 2x2x1 denotes 2 links in the x and y dimensions and one in the z dimension."},
        {"hyperx:local_ports",  "Number of endpoints attached to each router."},
        {"hyperx:algorithm",    "Routing algorithm to use.", "DOR"},

        {"shape",        "Shape of the mesh specified as the number of routers in each dimension, where each dimension is separated by a colon.  For example, 4x4x2x2.  Any number of dimensions is supported."},
        {"width",        "Number of links between routers in each dimension, specified in same manner as for shape.  For example, 2x2x1 denotes 2 links in the x and y dimensions and one in the z dimension."},
        {"local_ports",  "Number of endpoints attached to each router."},
        {"algorithm",    "Routing algorithm to use.", "DOR"}
    )

    enum RouteAlgo {
        DOR,
        DORND,
        MINA,
        VALIANT,
        DOAL,
        VDAL
    };

private:
    int router_id;
    int* id_loc;

    int dimensions;
    int* dim_size;
    int* dim_width;
    int total_routers;

    int* port_start; // where does each dimension start

    int num_local_ports;
    int local_port_start;

    int const* output_credits;
    int const* output_queue_lengths;
    int num_vcs;
    int num_vns;

    RNG::SSTRandom* rng;
    RNGFunc* rng_func;

    struct vn_info {
        int start_vc;
        int num_vcs;
        RouteAlgo algorithm;
    };

    vn_info* vns;

    // Each item in the vector represents a single non-host port.  It
    // tracks what routers in that dimension are reachable.  This will
    // be all 1's if there are no failed links.  A failed port will be
    // all 0's.  Otherwise, the bit will be 1 if the corresponding
    // router is reachable with 1 or 2 hops.  If failed links make it
    // impossible to reach a router in 2 or fewer hops through this
    // port, the bit will be a 0.
    std::vector<uint64_t> reachable_routers_in_dim;
    bool config_failed_links;

public:
    topo_hyperx(ComponentId_t cid, Params& p, int num_ports, int rtr_id, int num_vns);
    ~topo_hyperx();

    virtual void route_packet(int port, int vc, internal_router_event* ev);
    virtual internal_router_event* process_input(RtrEvent* ev);

    virtual void routeInitData(int port, internal_router_event* ev, std::vector<int> &outPorts);
    virtual internal_router_event* process_InitData_input(RtrEvent* ev);

    virtual PortState getPortState(int port) const;
    virtual int getEndpointID(int port);

    virtual void setOutputBufferCreditArray(int const* array, int vcs);
    virtual void setOutputQueueLengthsArray(int const* array, int vcs);

    virtual void getVCsPerVN(std::vector<int>& vcs_per_vn) {
        for ( int i = 0; i < num_vns; ++i ) {
            vcs_per_vn[i] = vns[i].num_vcs;
        }
    }

protected:
    virtual int choose_multipath(int start_port, int num_ports);

private:
    // void idToLocation(int id, int *location) const;
    void idToLocation(int rtr_id, int* location) const;
    void parseDimString(const std::string &shape, int *output) const;
    int get_dest_router(int dest_id) const;
    int get_dest_local_port(int dest_id) const;
    inline int get_port_for_dim_index(int dimension, int index, int slice)
    {
        int offset = index - ((index > id_loc[dimension]) ? 1 : 0);
        offset *= dim_width[dimension];
        return port_start[dimension] + offset + slice;
    }

    std::pair<int,int> routeDORBase(int* dest_loc);
    void routeDOR(int port, int vc, topo_hyperx_event* ev);
    void routeDORND(int port, int vc, topo_hyperx_event* ev);
    void routeMINA(int port, int vc, topo_hyperx_event* ev);
    void routeDOAL(int port, int vc, topo_hyperx_event* ev);
    void routeVDAL(int port, int vc, topo_hyperx_event* ev);
    void routeValiant(int port, int vc, topo_hyperx_event* ev);
};

}
}

#endif // COMPONENTS_MERLIN_TOPOLOGY_MESH_H
