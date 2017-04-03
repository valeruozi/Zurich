import zhinst.ziPython, zhinst.utils
from numpy import *
import time

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
             # [['/', self.device, '/sigouts/0/enables/*'], 0], #signal output, switches a channel of the mixer off
             # [['/', self.device, '/sigouts/1/enables/*'], 0]
        ]
        daq.set(general_setting)
    
        '''Set test settings''' #DA MODIFICARE IN BASE ALLE MISURE CHE SI VOLGIONO FARE
                                #SISTEMARE: ORDER
        t1_sigOutIn_setting = [ 
            [['/', self.device, '/sigins/',self.c,'/diff'], 0], #sigins = node of a signal input, diff = boolean value switching differential input mode
            [['/', self.device, '/sigins/', self.c, '/add'], 0],
            [['/', self.device, '/sigins/',self.c,'/imp50'], 1], #boolean value enabling 50Ohm input impedance termination
            [['/', self.device, '/sigins/',self.c,'/ac'], 0], #ac = boolean value setting for AC coupling of the signal  input
            [['/', self.device, '/sigins/',self.c,'/range'], 2], #voltage range of the signal input (max = 2)


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
            #[['/', self.device, '/sigouts/',self.c,'/add'], 0], #switches the output adder off
            #[['/', self.device, '/sigouts/',self.c,'/on'], 1], #switches the output on
            #[['/', self.device, '/sigouts/',self.c,'/enables/',self.c], 1], #switches a channel of the mixer on
            #[['/', self.device, '/sigouts/',self.c,'/range'], 1], #selects the ouput range for the signal output
            #[['/', self.device, '/sigouts/',self.c,'/amplitudes/',self.c], self.amplitude], #fraction of the output range added to the output signal
        ]
        self.daq.set(t1_sigOutIn_setting);
    
        '''Wait 1s to get a settled lowpass filter'''
        time.sleep(1)
    
        '''Clean queue'''
        self.daq.flush()
        
    def get_measure(self): #CAMBIARE SAMPLE #SYNC command to clear data befor polling??
        '''Subscribe to scope''' #Subscribe and unsubscibe are used to select the nodes from
        self.path0 = '/' + self.device + '/demods/'+ self.c + '/sample'   # which data should be recorded
                                                                            #sample of the demodulator are given out at this node
        self.daq.subscribe(self.path0)
        '''Poll data for 1s, second parameter is poll timeout in [ms] (recomended value is 500ms) '''
        self.DataDict = self.daq.poll(1,500); #Poll returns data for 1s and any data that
                                                # was already in the buffer since the last poll      
        '''Unsubscribe to scope'''
        self.daq.unsubscribe(self.path0)
     

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
device = 'DEV555'
LockIn = HF2LI(daq,device,1) #channel = 1
LockIn.inizialize(1e5)
LockIn.get_measure()
values = LockIn.DataDict
