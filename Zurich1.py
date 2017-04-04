import zhinst.ziPython, zhinst.utils
import numpy as np
import time
import matplotlib.pyplot as plt

class HF2LI:
    def __init__(self,daq,device,channel):
        self.daq = daq
        self.device = device
        self.channel=channel
        self.updated=0
    
    def inizialize(self,frequency,tc,rate):
        self.frequency = frequency # es = 1e5
        self.c=str(self.channel-1)
        self.c1 = str(self.channel)
        self.amplitude=1
        self.rate = rate # es = 200
        self.tc = tc #es = 0.01
        '''Disable all outputs and all demods'''
        general_setting = [
             [['/', self.device, '/demods/0/trigger'], 0], #Demods = output 'trigger' of a demodulator
             [['/', self.device, '/demods/1/trigger'], 0], #0,1,2... all the bits are set to zero, meaning that the
             [['/', self.device, '/demods/2/trigger'], 0], #demodulator data is sent continuously
             [['/', self.device, '/demods/3/trigger'], 0],
             [['/', self.device, '/demods/4/trigger'], 0],
             [['/', self.device, '/demods/5/trigger'], 0],
             [['/', self.device, '/sigouts/0/enables/*'], 0], #signal output, switches a channel of the mixer off
             [['/', self.device, '/sigouts/1/enables/*'], 0]
        ]
        self.daq.set(general_setting)
    
        '''Set test settings'''
        t1_sigIn_setting = [ 
#            [['/', self.device, '/sigins/',self.c,'/diff'], 0], #sigins = node of a signal input, diff = boolean value switching differential input mode
#            [['/', self.device, '/sigins/',self.c,'/imp50'], 1], #boolean value enabling 50Ohm input impedance termination
            [['/', self.device, '/sigins/',self.c,'/ac'], 0], #ac = boolean value setting for AC coupling of the signal  input
            [['/', self.device, '/sigins/',self.c,'/range'], 2*self.amplitude], #voltage range of the signal input (max = 2)


            [['/', self.device, '/demods/', self.c, '/enable'], 1],
            [['/', self.device, '/demods/',self.c,'/order'], 8], #order of the low pass filter =12db/oct slope
            [['/', self.device, '/demods/',self.c,'/timeconstant'], self.tc], #time constant fo the low pass filter (default = 0.010164)
            [['/', self.device, '/demods/',self.c,'/rate'], self.rate], #number of the output values sent to the computer per second
            [['/', self.device, '/demods/',self.c,'/adcselect'], self.channel-1],
            [['/', self.device, '/demods/',self.c,'/oscselect'], self.channel-1],
            [['/', self.device, '/demods/',self.c,'/harmonic'], 1],

            [['/', self.device, '/oscs/',self.c,'/freq'], self.frequency],

            [['/', self.device, '/auxouts/', self.c, '/outputselect'], 2], #Output = R
            [['/', self.device, '/auxouts/', self.c1, '/outputselect'], 3], #Output = Theta
            
            [['/', self.device, '/sigouts/0/on'], 0], #signal output, switches a channel of the mixer off
            [['/', self.device, '/sigouts/1/on'], 0]
           # [['/', self.device, '/sigouts/',self.c,'/add'], 0], #switches the output adder off
           # [['/', self.device, '/sigouts/',self.c,'/on'], 1], #switches the output on
           # [['/', self.device, '/sigouts/',self.c,'/enables/',self.c], 1], #switches a channel of the mixer on
           # [['/', self.device, '/sigouts/',self.c,'/range'], 1], #selects the ouput range for the signal output
           # [['/', self.device, '/sigouts/',self.c,'/amplitudes/',self.c], self.amplitude], #fraction of the output range added to the output signal
        ]
        self.daq.set(t1_sigIn_setting)
    
        '''Wait 1s to get a settled lowpass filter'''
        time.sleep(10*self.tc)
    
#        '''Clean queue'''
#        self.daq.flush()
        
    def get_measure(self):  #NON HA MOLTO SENSO

        # Perform a global synchronisation between the device and the data server:
        # Ensure that 1. the settings have taken effect on the device before issuing
        # the poll() command and 2. clear the API's data buffers. Note: the sync()
        # must be issued after waiting for the demodulator filter to settle above.
        daq.sync()

        '''Subscribe to the demodulator's sample node path''' #Subscribe and unsubscibe are used to select the nodes from
        self.path0 = '/' + self.device + '/demods/'+ self.c + '/sample'   # which data should be recorded
                                                                            #sample of the demodulator are given out at this node
        self.daq.subscribe(self.path0)
        '''Poll data for 1s, second parameter is poll timeout in [ms] (recomended value is 500ms) '''
        self.DataDict = self.daq.poll(1,500); #Poll returns data for 1s and any data that
                                                # was already in the buffer since the last poll      
        '''Unsubscribe from all paths'''
        self.daq.unsubscribe('*')

        self.sample = self.DataDict[self.path0]

        self.sample['R'] = np.abs(sample['x'] + 1j * sample['y'])
        self.sample['phi'] = np.angle(sample['x'] + 1j * sample['y'])
        print("Average measured RMS amplitude is {:.3e} V.".format(np.mean(sample['R'])))

    def get_sweep(self,start,stop,samplecount):
        
        self.start = start #es = 4e3
        self.stop = stop # es = 50e6
        self.samplecount = samplecount #es = 100
        #sweep (list of dict): A list of demodulator sample dictionaries. Each
        #entry in the list correspond to the result of a single sweep and is a
        #dict containing a demodulator sample.
        self.osc_index = 0
        # Create an instance of the Sweeper Module (ziDAQSweeper class)
        self.sweeper = self.daq.sweep()

        # Configure the Sweeper Module's parameters.
        # Set the device that will be used for the sweep - this parameter must be set.
        self.sweeper.set('sweep/device', self.device)
        # Specify the `gridnode`: The instrument node that we will sweep, the device
        # setting corresponding to this node path will be changed by the sweeper.
        self.sweeper.set('sweep/gridnode', 'oscs/%d/freq' %self.osc_index)
        # Set the `start` and `stop` values of the gridnode value interval we will use in the sweep.
        self.sweeper.set('sweep/start', self.start)
        self.sweeper.set('sweep/stop', self.stop)
        # Set the number of points to use for the sweep, the number of gridnode
        # setting values will use in the interval (`start`, `stop`).
        self.sweeper.set('sweep/samplecount', self.samplecount)
        # Specify logarithmic spacing for the values in the sweep interval.
        self.sweeper.set('sweep/xmapping', 1)
        # Automatically control the demodulator bandwidth/time constants used.
        # 0=manual, 1=fixed, 2=auto
        # Note: to use manual and fixed, sweep/bandwidth has to be set to a value > 0.
        self.sweeper.set('sweep/bandwidthcontrol', 2)
        # Sets the bandwidth overlap mode (default 0). If enabled, the bandwidth of
        # a sweep point may overlap with the frequency of neighboring sweep
        # points. The effective bandwidth is only limited by the maximal bandwidth
        # setting and omega suppression. As a result, the bandwidth is independent
        # of the number of sweep points. For frequency response analysis bandwidth
        # overlap should be enabled to achieve maximal sweep speed (default: 0). 0 =
        # Disable, 1 = Enable.
        self.sweeper.set('sweep/bandwidthoverlap', 0)

        # Sequential scanning mode (as opposed to binary or bidirectional).
        self.sweeper.set('sweep/scan', 0)
        # Specify the number of sweeps to perform back-to-back.
        self.loopcount = 1
        self.sweeper.set('sweep/loopcount', self.loopcount)
        # Settiling time before measurement is performed
        self.sweeper.set('sweep/settling/time', 0)
        # The sweep/settling/inaccuracy' parameter defines the settling time the
        # sweeper should wait before changing a sweep parameter and recording the next
        # sweep data point. The settling time is calculated from the specified
        # proportion of a step response function that should remain. The value
        # provided here, 0.001, is appropriate for fast and reasonably accurate
        # amplitude measurements. For precise noise measurements it should be set to
        # ~100n.
        # Note: The actual time the sweeper waits before recording data is the maximum
        # time specified by sweep/settling/time and defined by
        # sweep/settling/inaccuracy.
        self.sweeper.set('sweep/settling/inaccuracy', 0.001)
        # Set the minimum time to record and average data to 10 demodulator
        # filter time constants.
        self.sweeper.set('sweep/averaging/tc', 10)
        # Minimal number of samples that we want to record and average is 100. Note,
        # the number of samples used for averaging will be the maximum number of
        # samples specified by either sweep/averaging/tc or sweep/averaging/sample.
        self.sweeper.set('sweep/averaging/sample', 100)

        # Now subscribe to the nodes from which data will be recorded. Note, this is
        # not the subscribe from ziDAQServer; it is a Module subscribe. The Sweeper
        # Module needs to subscribe to the nodes it will return data for.x
        self.path = '/%s/demods/%d/sample' %(self.device, self.channel-1)
        self.sweeper.subscribe(self.path)

        # Start the Sweeper's thread.
        self.sweeper.execute()

        self.start = time.time()
        self.timeout = 101  # [s] SET TO 60
        print("Will perform ", self.loopcount, "sweeps...")
        while not self.sweeper.finished():  # Wait until the sweep is complete, with timeout.
            time.sleep(1)
            progress = self.sweeper.progress()
            print("Individual sweep progress: {:.2%}.".format(progress[0]))
            # Here we could read intermediate data via:
#            self.data = self.sweeper.read(True)
#            print("Intermediate data:", self.data)
            # and process it while the sweep is completing.
            # if device in data:
            # ...
            if (time.time() - self.start) > self.timeout:
                # If for some reason the sweep is blocking, force the end of the
                # measurement.
                print("\nSweep still not finished, forcing finish...")
                self.sweeper.finish()
        print("")

        # Read the sweep data. This command can also be executed whilst sweeping
        # (before finished() is True), in this case sweep data up to that time point
        # is returned. It's still necessary still need to issue read() at the end to
        # fetch the rest.
        return_flat_dict = True
        self.data = self.sweeper.read(return_flat_dict)
        self.sweeper.unsubscribe(self.path)

        # Stop the sweeper thread and clear the memory.
        self.sweeper.clear()
         # Check the dictionary returned is non-empty.
        assert self.data, "read() returned an empty data dictionary, did you subscribe to any paths?"
        # Note: data could be empty if no data arrived, e.g., if the demods were
        # disabled or had rate 0.
#        return self.data
        assert self.path in self.data, "No sweep data in data dictionary: it has no key '%s'" % self.path
        self.samples = self.data[self.path]
        print("Returned sweeper data contains", len(self.samples), "sweeps.")
        assert len(self.samples) == self.loopcount, \
            "The sweeper returned an unexpected number of sweeps: `%d`. Expected: `%d`." % (len(self.samples), self.loopcount)
        for i in range(0, len(self.samples)):
             self.meas = Measure(np.abs(self.samples[i][0]['x'] + 1j*self.samples[i][0]['y']),np.angle(self.samples[i][0]['x'] + 1j*self.samples[i][0]['y']))
        return self.meas
            
    def do_plot_sweep(self):
        for i in range(0, len(self.samples)):
             R = np.abs(self.samples[i][0]['x'] + 1j*self.samples[i][0]['y'])
             phi = np.angle(self.samples[i][0]['x'] + 1j*self.samples[i][0]['y'])
             frequency = self.samples[i][0]['frequency']
             plt.subplot(2, 1, 1)
             plt.semilogx(frequency, R)
             plt.subplot(2, 1, 2)
             plt.semilogx(frequency, phi)
        plt.subplot(2, 1, 1)
        plt.title('Results of %d sweeps.' % len(self.samples))
        plt.grid(True)
        plt.ylabel(r'Demodulator R ($V_\mathrm{RMS}$)')
        # plt.ylim(0.0, np.amax(R))
        plt.autoscale()
        plt.subplot(2, 1, 2)
        plt.grid(True)
        plt.xlabel('Frequency ($Hz$)')
        plt.ylabel(r'Demodulator Phi (radians)')
        plt.autoscale()
        plt.draw()
        plt.show()

     

class Measure: 
    def __init__(self,A,B):
        self.A = A
        self.B = B

class Sweep: 
    def __init__(self,a,b,npoints,sweep_type,scale_type): #Unit Hz
        self.start = a
        self.stop = b 
        self.center = a
        self.span = b
        self.npoints = npoints
        '''Sets the sweep type'''
        self.sweep_type = sweep_type 
        self.scale_type = scale_type

'''Open connection to ziServer''' #Data Server Port = 8005
daq = zhinst.ziPython.ziDAQServer('localhost', 8005) 
'''Detect device''' #device = device ID
#device = zhinst.utils.autoDetect()
device = 'dev555'
LockIn = HF2LI(daq,device,1) #channel = 1
LockIn.inizialize(1e3,0.01,100)
# LockIn.get_measure()
# values = LockIn.DataDict
Values = LockIn.get_sweep(1e3,1e6,10)
LockIn.do_plot_sweep()
