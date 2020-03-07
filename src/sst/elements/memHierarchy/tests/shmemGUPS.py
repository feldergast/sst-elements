import sst
from sst.merlin import *

import KingsleyNode 

# Define SST core options
sst.setProgramOption("timebase", "1ps")
sst.setProgramOption("stopAtCycle", "0 ns")

networkParams = {
    "packetSize" : "2048B",
    "link_bw" : "16GB/s",
    "xbar_bw" : "16GB/s",
    "link_lat" : "40ns",
    "input_latency" : "50ns",
    "output_latency" : "50ns",
    "flitSize" : "8B",
    #"input_buf_size" : "30KB",
    #"output_buf_size" : "30KB",
    "input_buf_size" : "14KB",
    "output_buf_size" : "14KB",
}

sst.merlin._params["link_lat"] = networkParams['link_lat']
sst.merlin._params["link_bw"] = networkParams['link_bw']
sst.merlin._params["xbar_bw"] = networkParams['xbar_bw']
sst.merlin._params["flit_size"] = networkParams['flitSize']
sst.merlin._params["input_latency"] = networkParams['input_latency']
sst.merlin._params["output_latency"] = networkParams['output_latency']
sst.merlin._params["input_buf_size"] = networkParams['input_buf_size']
sst.merlin._params["output_buf_size"] = networkParams['output_buf_size']
sst.merlin._params["num_dims"] = "2"
sst.merlin._params["torus:shape"] = "2x1" 
sst.merlin._params["torus:width"] = "1x1"
sst.merlin._params["torus:local_ports"] = "1" 

topo = topoTorus()
topo.prepParams()

numNodes=2
pesPerNode=36
nicAddr=0x100000000
cmdQsize =64 
gupsMemSize=0x100000

ep = KingsleyNode.Endpoint( numNodes, pesPerNode, nicAddr, cmdQsize, gupsMemSize, 
	networkParams['link_bw'], networkParams['input_buf_size'], networkParams['output_buf_size'], 1 )

def setNode( nodeId ):
    print 'setNode', nodeId
    return ep;

print 'call topo.setEndPointFunc()'
topo.setEndPointFunc( setNode )
print 'call topo.build()'
topo.build()

# Enable SST Statistics Outputs for this simulation
sst.setStatisticLoadLevel(16)
sst.setStatisticOutput("sst.statOutputCSV");
sst.setStatisticOutputOptions({
    "filepath" : "stats.out",
    "separator" : ", "
})

#sst.enableStatisticForComponentType("memHierarchy.DirectoryController",'directory_cache_hits', {"type":"sst.AccumulatorStatistic","rate":"0ns"})
#sst.enableStatisticForComponentType("memHierarchy.DirectoryController",'mshr_hits', {"type":"sst.AccumulatorStatistic","rate":"0ns"})

#sst.enableStatisticForComponentType("miranda.shmemGUPS",'loopLatency', #{"type":"sst.AccumulatorStatistic","rate":"0ns"})
#{"type":"sst.HistogramStatistic",
#"rate":"0ns",
#"binwidth":"10",
#"numbins":"100"}
#)
#sst.enableStatisticForComponentType("miranda.shmemGUPS",'readLatency', #{"type":"sst.AccumulatorStatistic","rate":"0ns"})
#{"type":"sst.HistogramStatistic",
#"rate":"0ns",
#"binwidth":"10",
#"numbins":"100"}
#)

#sst.enableStatisticForComponentType("miranda.shmemGUPS",'fenceLatency',#{"type":"sst.AccumulatorStatistic","rate":"0ns"})
#{"type":"sst.HistogramStatistic",
#"rate":"0ns",
#"binwidth":"10",
#"numbins":"100"}
#)

#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'hostCmdQ', {"type":"sst.AccumulatorStatistic","rate":"0ns"})
#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'headUpdateQ', {"type":"sst.AccumulatorStatistic","rate":"0ns"})
#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'pendingMemResp', {"type":"sst.AccumulatorStatistic","rate":"0ns"})
#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'pendingCmds', {"type":"sst.AccumulatorStatistic","rate":"0ns"})

#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'localQ_0', {"type":"sst.AccumulatorStatistic","rate":"0ns"})
#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'localQ_1', {"type":"sst.AccumulatorStatistic","rate":"0ns"})
#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'remoteQ_0', {"type":"sst.AccumulatorStatistic","rate":"0ns"})
#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'remoteQ_1', {"type":"sst.AccumulatorStatistic","rate":"0ns"})

#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'pendingMemResp', #{"type":"sst.AccumulatorStatistic","rate":"0ns"})
#{"type":"sst.HistogramStatistic",
#"rate":"0ns",
#"binwidth":"4",
#"numbins":"20"}
#)

sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'cyclePerIncOpRead',#{"type":"sst.AccumulatorStatistic","rate":"0ns"})
{"type":"sst.HistogramStatistic",
"rate":"0ns",
"binwidth":"10",
"numbins":"400"}
)
sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'cyclePerIncOp',#{"type":"sst.AccumulatorStatistic","rate":"0ns"})
{"type":"sst.HistogramStatistic",
"rate":"0ns",
"binwidth":"10",
"numbins":"400"}
)

#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'addrIncOp',{"type":"sst.AccumulatorStatistic","rate":"0ns"})

#sst.enableStatisticForComponentType("memHierarchy.ShmemNic",'addrIncOp',
#{"type":"sst.HistogramStatistic",
#"rate":"0ns",
#"binwidth":0x100000/4,
#"numbins":36*4}
#)

#sst.enableStatisticForComponentType("miranda.shmemGUPS",'addrIncOp',
#{"type":"sst.HistogramStatistic",
#"rate":"0ns",
#"binwidth":32768,
#"numbins":32}
#)
