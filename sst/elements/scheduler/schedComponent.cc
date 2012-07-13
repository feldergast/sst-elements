// Copyright 2010 Sandia Corporation. Under the terms
// of Contract DE-AC04-94AL85000 with Sandia Corporation, the U.S.
// Government retains certain rights in this software.
// 
// Copyright (c) 2010, Sandia Corporation
// All rights reserved.
// 
// This file is part of the SST software package. For license
// information, see the LICENSE file in the top level directory of the
// distribution.

#include "sst_config.h"
#include "sst/core/serialization/element.h"
#include <assert.h>
#include <fstream>
#include <iostream>

//#include <QFileSystemWatcher>

#include "sst/core/element.h"

#include "misc.h"
#include "PQScheduler.h"
#include "EASYScheduler.h"
#include "schedComponent.h"
#include "SimpleAllocator.h"
#include "SimpleMachine.h"

using namespace SST;
using namespace std;

Machine* schedComponent::getMachine() {
  return machine;
}

schedComponent::schedComponent(ComponentId_t id, Params_t& params) :
  Component(id) {

  if ( params.find("traceName") == params.end() ) {
    _abort(event_test,"couldn't find trace name\n");
  }


  // tell the simulator not to end without us
  registerExit();

  // configure links
  bool done = 0;
  int count = 0;
  // connect links till we can't find any
  printf("Scheduler looking for link...");
  while (!done) {
    char name[50];
    snprintf(name, 50, "nodeLink%d", count);
    printf(" %s", name);
    SST::Link *l = configureLink( name, 
				  new Event::Handler<schedComponent,int>(this,
									 &schedComponent::handleCompletionEvent, count) );
    if (l) {
      nodes.push_back(l);
      count++;
    } else {
      printf("(no %s)", name);
      done = 1;
    }
  }

  selfLink = configureSelfLink("linkToSelf",
			       new Event::Handler<schedComponent>(this,
								  &schedComponent::handleJobArrivalEvent) );
  selfLink->setDefaultTimeBase(registerTimeBase("1 s"));

  machine = new SimpleMachine(nodes.size(), this);
  scheduler = new EASYScheduler(EASYScheduler::JobComparator::Make("fifo"));
  theAllocator = new SimpleAllocator(dynamic_cast<SimpleMachine*>(machine));
  string trace = params[ "traceName" ].c_str();
  char timestring[] = "time";
  stats = new Statistics(machine, scheduler, theAllocator, trace, timestring);
  ifstream input;
  char* inputDir = getenv("SIMINPUT");
  if(inputDir != NULL) {
    string fullName = inputDir + trace;
    input.open(fullName.c_str());
  }
  if(!input.is_open())
    input.open(trace.c_str());  //try without directory                     
  if(!input.is_open())
    error("Unable to open file " + trace);
  
  printf("\nScheduler Detects %d nodes\n", (int)nodes.size());
    
  machine -> reset();
  scheduler -> reset();

  string line;
  while(!input.eof()) {
    getline(input, line);
    newJobLine( line );
  }
  input.close();
  
  /*QFileSystemWatcher monitor;
  monitor.addPath( fullName.c_str() );
  
  QObject::connect( &monitor, SIGNAL( QFileSystemWatcher::fileChanged ( QString ), this,  )*/
}

schedComponent::schedComponent() :
    Component(-1)
{
    // for serialization only
}



bool schedComponent::newJobLine( std::string line ){
  if(line.find_first_not_of(" \t\n") == string::npos)
    return false;

  long arrivalTime;
  int procsNeeded;
  long runningTime;
  long estRunningTime;
  int num = sscanf(line.c_str(), "%ld %d %ld %ld", &arrivalTime,
                   &procsNeeded, &runningTime, &estRunningTime);
  if(num < 3)
    error("Poorly formatted input line: " + line);
  if(num == 3)
    jobs.push_back(Job(arrivalTime, procsNeeded, runningTime, runningTime));
  else   //read all 4                                                        
    jobs.push_back(Job(arrivalTime, procsNeeded, runningTime, estRunningTime));

  //validate                                                                  
  Job* j = &jobs.back();
  char mesg[100];
  bool ok = true;
  if (j -> getProcsNeeded() <= 0) {
    sprintf(mesg, "Job %ld  requests %d processors; ignoring it",
            j -> getJobNum(), j -> getProcsNeeded());
    warning(mesg);
    jobs.pop_back();
    ok = false;
  }
  if (ok && runningTime < 0) {  //time 0 also strange, but perhaps rounded down     
    sprintf(mesg, "Job %ld  has running time of %ld; ignoring it",
            j -> getJobNum(), runningTime);
    warning(mesg);
    jobs.pop_back();
    ok = false;
  }
  if(ok && j -> getProcsNeeded() > machine -> getNumFreeProcessors()) {
    sprintf(mesg,
            "Job %ld requires %d processors but only %d are in the machine",
            j -> getJobNum(), j -> getProcsNeeded(),
            machine -> getNumFreeProcessors());
    error(mesg);
  }
  if (ok) {
    ArrivalEvent* ae = new ArrivalEvent(j -> getArrivalTime(), jobs.size()-1);
    selfLink->Send(j -> getArrivalTime(), ae);
  }
  
  return ok;
}



// incoming events are scanned and deleted. ev is the returned event,
// node is the node it came from.
void schedComponent::handleCompletionEvent(Event *ev, int node) {
  CompletionEvent *event = dynamic_cast<CompletionEvent*>(ev);
  if (event) {
    int jobNum = event->jobNum;
      if(runningJobs[jobNum].ai == NULL)
      {
        runningJobs.erase(jobNum);
        return; //this event has already stopped (probably faulted)
      }
    if ((--(runningJobs[jobNum].i)) == 0) {
      AllocInfo *ai = runningJobs[jobNum].ai;
      runningJobs.erase(jobNum);
      machine->deallocate(ai);
      theAllocator->deallocate(ai);
      stats->jobFinishes(ai, getCurrentSimTime());
      scheduler->jobFinishes(ai->job, getCurrentSimTime(), machine);

      //tries to start job
      AllocInfo* allocInfo;
      do {
        allocInfo = scheduler -> tryToStart(theAllocator, getCurrentSimTime(), machine, stats);
      } while(allocInfo != NULL);
    }
    if(jobNum == jobs.back().jobNum)
    {
      while(!jobs.empty() && runningJobs.find(jobs.back().jobNum) == runningJobs.end())
        jobs.pop_back();
      if(jobs.empty())
      {
        unregisterExit();
      }
    }
  } else {
    //If it is not a completion it is (hopefully) a fault.
    //as far as the scheduler is concerned this is treated the same way
    //however, must send a kill event to tell all nodes with this job to
    //stop running (not all the nodes may have failed but all must stop)
    //for now, the job is dropped forever
    JobFaultEvent *event = dynamic_cast<JobFaultEvent*>(ev);
    if (event) {
      int jobNum = event->jobNum;
      if(jobNum == -1 )
        return; // the node that faulted was not running a job, nothing for 
                //scheduler, allocator, machine to do
      //force all nodes running the job to kill it
      AllocInfo *ai = runningJobs[jobNum].ai;
      if(ai == NULL)
      {
        runningJobs.erase(jobNum);
        return;
      }
      //if ai is NULL we already killed this job
      for (int i = 0; i < ai->job->getProcsNeeded(); ++i) {
        JobKillEvent *ec = new JobKillEvent(ai->job->getJobNum());
        nodes[ai->nodeIndices[i]]->Send(ec);
      }

      runningJobs.erase(jobNum);
      //char a;
      //cin >> a;
      machine->deallocate(ai);
      theAllocator->deallocate(ai);
      stats->jobFinishes(ai, getCurrentSimTime());
      scheduler->jobFinishes(ai->job, getCurrentSimTime(), machine);

      //tries to start job
      AllocInfo* allocInfo;
      do {
        allocInfo = scheduler -> tryToStart(theAllocator, getCurrentSimTime(), machine, stats);
      } while(allocInfo != NULL);
      if(jobNum == jobs.back().jobNum)
      {
        while(!jobs.empty() && runningJobs.find(jobs.back().jobNum) == runningJobs.end())
          jobs.pop_back();
        if(jobs.empty())
        {
          unregisterExit();
        }
      }
    } else {
      internal_error("S: Error! Bad Event Type!\n");
    }
  }  
}

void schedComponent::handleJobArrivalEvent(Event *ev) {
  ArrivalEvent *event = dynamic_cast<ArrivalEvent*>(ev);
  event -> happen(machine, theAllocator, scheduler, stats, &jobs[event->getJobIndex()]);
}

int schedComponent::Finish() {
  scheduler -> done();
  stats -> done();
  theAllocator -> done();
  return 0;
}


void schedComponent::startJob(AllocInfo* ai) {
  Job* j = ai->job;
  int* jobNodes = ai->nodeIndices;
  // send to each person in the node list
  for (int i = 0; i < j->getProcsNeeded(); ++i) {
    JobStartEvent *ec = new JobStartEvent(j->getActualTime(), j->getJobNum());
    nodes[jobNodes[i]]->Send(ec);
  }

  IAI iai;
  iai.i = j->getProcsNeeded();
  iai.ai = ai;
  runningJobs[j->getJobNum()] = iai;
}

/*
bool schedComponent::clockTic( Cycle_t ) {

  // send test jobs
  if (getCurrentSimTime() == 1) {
    // send to node 0
    // create the event
    SWFEvent *e = new SWFEvent;
    e->JobNumber = 1;
    e->RunTime = 10;
    // create the list of target nodes
    targetList_t nodeList;
    nodeList.push_back(0);
    // start the job
    startJob(e, nodeList);
  } else if (getCurrentSimTime() == 12) {
    printf("\n");
  } else if (getCurrentSimTime() == 13) {
    // send to odd nodes
    // create the event
    SWFEvent *e = new SWFEvent;
    e->JobNumber = 1;
    e->RunTime = 5;
    // create the list of target nodes
    targetList_t nodeList;
    for (int i = 0; i < nodes.size(); ++i) {
      if (i & 0x1) {
	nodeList.push_back(i);
      }
    }
    // start the job
    startJob(e, nodeList);
  }

  // end simulation after 1 hour of simulated time
  if (getCurrentSimTime() >= 3600) {
    unregisterExit();
  }

  // return false so we keep going
  return false;
}
*/

// Element Libarary / Serialization stuff

//BOOST_CLASS_EXPORT(ArrivalEvent)
BOOST_CLASS_EXPORT(schedComponent)

