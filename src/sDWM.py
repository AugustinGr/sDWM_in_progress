__author__ = 'ewan'
import matplotlib as mpl
if mpl.get_backend<>'agg':
    mpl.use('agg')
# mpl.use('WxAgg')
# mpl.interactive(True)
import matplotlib.pyplot as plt
import numpy as np
# print '\nBackend:\n' + mpl.get_backend() + '\n'
import WindFarm as wf
import WindTurbine as wt
#import matplotlib.pyplot as plt
from DWM_flowfield_farm import DWM_main_field_model, DWM_main_field_model_partly_dynamic
from math import pi, sqrt, isnan
from DWM_GClarsenPicks import get_Rw
from DWM_init_dict import init
import time
from scipy import io, interpolate
from DWM_misc import smooth, to_bool
import matplotlib.pylab as plt
import matplotlib._cntr as cntr
import multiprocessing

from ReadTurbulence import pre_init_turb, ReadMannInput, pre_init_turb_LES
from Wake_added_turbulence_Main import pre_init_turb_WaT


###########################################################################

def sDWM(derating,kwargs,xind):
    # ttt = time.time()
#     WD,WS,TI,WTcoord,WTG,HH,R,stab,accum,optim,
    WD = kwargs.get('WD')
    WS = kwargs.get('WS')
    TI = kwargs.get('TI')
    WTcoord = kwargs.get('WTcoord')
    WTG = kwargs.get('WTG')
    HH = kwargs.get('HH')
    R = kwargs.get('R')
    stab = kwargs.get('stab')
    accum = kwargs.get('accum')
    optim = to_bool(kwargs.get('optim'))
    dynamic = to_bool(kwargs.get('dynamic'))
    Meandering_turb_box_name=kwargs.get('Meandering_turb_box_name')
    WaT_turb_box_name = kwargs.get('WaT_turb_box_name')

    # WT = wt.WindTurbine('Vestas v80 2MW offshore','V80_2MW_offshore.dat',70,40)
    # WF = wf.WindFarm('Horns Rev 1','HR_coordinates.dat',WT)
    WT = wt.WindTurbine('Windturbine','../WT-data/'+WTG+'/'+WTG+'_PC.dat',HH,R)
    WF = wf.WindFarm('Windfarm',WTcoord,WT)

    #########################################################################################################
    if dynamic:
        if Meandering_turb_box_name!=None:
            print '# ------------------------------------------------------------------------------------------------ #'
            print '# -------------------------- Pre Init for Meandering --------------------------------------------- #'
            if Meandering_turb_box_name[1] == 'Mann_Box':
                filename = Meandering_turb_box_name[0]  # must come from sDWM Input
                #R_wt = 46.5  # can come from sDWM
                #WTG = 'NY2'  # can come from sDWM
                #HH = 90.  # Hub height    # can come from sDWM

                Rw = 1.  # try with no expansion
                WF.U_mean = WS
                WF.WT_R = WT.R
                WF.WT_Rw = Rw
                WF.TI = TI

                WT = wt.WindTurbine('Windturbine', '../WT-data/' + WTG + '/' + WTG + '_PC.dat', HH, WT.R)  # already present in sDWM
                TurBox, WF = pre_init_turb(filename, WF, WT)
            elif Meandering_turb_box_name[1] == 'LES_Box':
                filename = Meandering_turb_box_name[0]  # must come from sDWM Input
                # R_wt = 46.5  # can come from sDWM
                # WTG = 'NY2'  # can come from sDWM
                # HH = 90.  # Hub height    # can come from sDWM

                Rw = 1.  # try with no expansion
                WF.U_mean = WS
                WF.WT_R = WT.R
                WF.WT_Rw = Rw
                WF.TI = TI

                WT = wt.WindTurbine('Windturbine', '../WT-data/' + WTG + '/' + WTG + '_PC.dat', HH,
                                    WT.R)  # already present in sDWM
                TurBox, WF = pre_init_turb_LES(filename, WF, WT)
            print '# -------------------------- End Pre Init for Meandering ----------------------------------------- #'
            print '# ------------------------------------------------------------------------------------------------ #'
        else:
            print '# -------------------------- Used Saved DATA for MEANDERING / No Meandering ---------------------- #'
            TurBox = ReadMannInput('1028')

        if WaT_turb_box_name!= None:
            print '# ------------------------------------------------------------------------------------------------ #'
            print '# -------------------------- Pre Init for WaT ---------------------------------------------------- #'
            MannBox = pre_init_turb_WaT(WaT_turb_box_name)
            MannBox.R_ref = R
            print '# -------------------------- End Pre Init for WaT ------------------------------------------------ #'
            print '# ------------------------------------------------------------------------------------------------ #'
        else:
            MannBox = None
        print 'TI Input:', TI
        #TI = TurBox.TI
        print 'TI from TurbBox', TI

    ####################################################################################################################
    if optim is True:
        print 'Performing optimization'
        WT.CP = np.load('../WT-data/'+WTG+'/'+WTG+'_CP.npy')
        WT.CT = np.load('../WT-data/'+WTG+'/'+WTG+'_CT.npy')

        #print 'Cp and then Ct are :'
        #print WT.CP
        #print WT.CT

        WT.lambdaf3=WT.CP[:,:,0]
        WT.PITCH3=WT.CP[:,:,1]
        WT.CP3=WT.CP[:,:,2]
        WT.CT3=WT.CT[:,:,2]
        WT.CP3[WT.CP3>(16./27.)]=0
        WT.CP3[np.isnan(WT.CP3)]=0
        WT.CT3[np.isnan(WT.CT3)]=0
        WT.CPc = cntr.Cntr(WT.PITCH3,WT.lambdaf3,WT.CP3)
        WT.CTc=cntr.Cntr(WT.PITCH3,WT.lambdaf3,WT.CT3)
    elif optim is False:
        print 'Not Performing optimization'
        derating=1.0*np.ones((WF.nWT))
        WT.CP = None
        WT.CT = None

    # Scaling wind farm to NREL's rotor size
    if 'Lill' in WTcoord:
        WF.vectWTtoWT=WF.vectWTtoWT*(WT.R/46.5) # 46.5 is the Lillgrund nominal radius of SWT turbine
        #print WT.R/46.5: 1.0
        #print 'WF.vectWTtoWT: ', WF.vectWTtoWT
        #raw_input('...')


    # Compute distance WT to WT in mean flow coordinate system
    distFlowCoord, nDownstream, id0= WF.turbineDistance(WD)
    """
    print 'distflowcoord', distFlowCoord
    print 'ndownstream', nDownstream
    print 'id0', id0
    raw_input('...')
    #"""

    # Init dictionnaries
    deficits, turb, inlets_ffor, inlets_ffor_deficits,inlets_ffor_turb,out, DWM, ID_waked, ID_wake_adj, Farm_p_out, WT_p_out, Vel_out,WT_pitch_out,WT_RPM_out=init(WF)

    #raw_input('entry')

    # Extreme wake to define WT's in each wake, including partial wakes
    # but it doesn't keep Rw, however Rw is an important quantity used to model Meandering Dynamic!
    # I don't really understant what is following. (it comes from 2009 simple analytical wake model Glarsen)
    # it seems to show wich wake we need for each iteration?
    # To keep the thoughts of ewma I keep this part but I am not sure about this...
    # For this reason we have to know TI from the turbulent box before this step.

    ID_wake = {id0[i]:(get_Rw(x=distFlowCoord[0,id0[i],:],
                                  R=2*WF.WT.R,TI=TI,CT=WT.get_CT(WS),pars=[0.435449861,0.797853685,-0.124807893,0.136821858,15.6298,1.0])>\
                                  np.abs(distFlowCoord[1,id0[i],:])).nonzero()[0] \
                   for i in range(WF.nWT)}
    #"""
    print 'ID_wake {id: id with a wake}: '
    print ID_wake
    print ID_wake[1]
    print distFlowCoord

    # Power output list
    Farm_p_out=0.
    WT_p_out=np.zeros((WF.nWT))
    WT_pitch_out=np.zeros((WF.nWT,2))
    WT_RPM_out=np.zeros((WF.nWT,2))
    Vel_out=np.zeros((WF.nWT))

    # COMPUTING TO PLOT
    """
    POWER_TURBINE = []
    VEL_plot=[]
    RPM_plot=[]
    PITCH_plot=[]
    #"""
    ## Main DWM loop over turbines
    FFOR_result = []
    print '############################################################################################################'
    print '# -------------------------- # MAIN LOOP OVER TURBINE PROCESSING # --------------------------------------- #'
    for iT in range(WF.nWT):
        print '# -------------------------- # PROCESSING for iteration '+str(iT)+' # -------------------------------- #'
        # Define flow case geometry
        cWT = id0[iT]

        #Radial coordinates in cWT for wake affected WT's
        x=distFlowCoord[0,cWT,ID_wake[cWT]]
        C2C   = distFlowCoord[1,cWT,ID_wake[cWT]]

        index_orig=np.argsort(x)
        x=np.sort(x)
        row= ID_wake[id0[iT]][index_orig]
        C2C=C2C[index_orig]

        # Wrapping the DWM core model with I/O
        par={
         'WS':WS,
         'TI':TI,
         'atmo_stab':stab,
         'WTG':WTG,      #'WTG':'NREL5MW',
         'WTG_spec': WT,
         'wtg_ind': row, # turbine index
         'hub_z':x/(2*WF.WT.R), # compute the flow field at downstream location of each downwind turbine !
         'hub_x': np.ceil((2*(max(abs(C2C))+WF.WT.R))/WF.WT.R)*0.5+C2C/(WF.WT.R), # lateral offset of each downwind turbine with respect to the most upstream turbine in the tree
         'C2C': C2C, # center 2 center distances between hubs
         'lx':np.ceil((2.*(max(abs(C2C))+WF.WT.R))/WF.WT.R), # length of the domain in lateral
         'ly':np.ceil((2.*(max(abs(C2C))+WF.WT.R))/WF.WT.R),  # length of the domain in longitudinal in D
         'wake_ind_setting':1,
         'accu_inlet': True,
         'derating': derating[row[0]],
         'optim': optim,
         'accu': accum, # type of wake accumulation
         'full_output': False, # Flag for generating the complete output with velocity deficit
         'iT': iT
        }
        ID_wake_adj[str(id0[iT])]=row
        print row
        #"""
        if dynamic:
            aero, meta, mfor, ffor, DWM, deficits, inlets_ffor, inlets_ffor_deficits, inlets_ffor_turb, turb, out, ID_waked = DWM_main_field_model_partly_dynamic(ID_waked,deficits,inlets_ffor,inlets_ffor_deficits,inlets_ffor_turb,turb,DWM,out, TurBox, WF, MannBox,**par)
            """
            if meta.iT == 0:
                FFOR_result = ffor.WS_axial_ffor
            else:
                FFOR_result[:,:,meta.iT:,:] = FFOR_result[:,:,meta.iT:,:] + ffor.WS_axial_ffor
            #raw_input('....')
            if meta.MEANDERING_Total_plot:

                plt.ion()
                plt.figure('Meandering draw in time for each turbine in the wake')

                x = ffor.x_vec
                y = ffor.y_vec
                # X, Y = np.meshgrid(x, y)
                X, Y = ffor.x_mat, ffor.y_mat
                ref_rotor_x_emitting = (meta.hub_x[0] + np.cos(np.linspace(-pi, pi))) / 2.
                ref_rotor_y_emitting = (meta.hub_y + np.sin(np.linspace(-pi, pi))) / 2.
                for i_z in np.arange(0, 3):
                    # for i_z in np.arange(0, meta.nz):
                    ref_rotor_x_concerned = (meta.hub_x[i_z] + np.cos(np.linspace(-pi, pi))) / 2.
                    ref_rotor_y_concerned = (meta.hub_y + np.sin(np.linspace(-pi, pi))) / 2.
                    for i_t in np.arange(0, meta.nt, 2):
                        plt.cla()
                        plt.clf()
                        print 'i_t = ', i_t
                        if True:
                            plt.subplot(121)
                            CS1 = plt.contourf(X, Y, FFOR_result[:, :, i_z, i_t], np.linspace(0., 1., 20))
                            plt.xlabel('x'), plt.ylabel('y'), plt.title(
                                'Axial WS FFoR for Turbine ' + str(meta.wtg_ind[i_z]))  # 7-iz
                            plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
                            plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
                            plt.legend()
                            plt.colorbar(CS1)
                            plt.draw()
                            plt.pause(0.0001)
            #"""
        else:
            aero, meta, mfor, ffor, DWM, deficits,inlets_ffor,inlets_ffor_deficits, inlets_ffor_turb,turb, out,ID_waked = DWM_main_field_model(ID_waked,deficits,inlets_ffor,inlets_ffor_deficits,inlets_ffor_turb,turb,DWM,out,**par)
            if meta.steadyBEM_AINSLIE:
                if meta.iT == 0:
                    FFOR_result = ffor.WS_axial_ffor
                else:
                    FFOR_result[:, :, meta.iT:, :] = FFOR_result[:, :, meta.iT:, :] + ffor.WS_axial_ffor
                # raw_input('....')
                if meta.MEANDERING_Total_plot:

                    plt.ion()
                    plt.figure('Meandering draw in time for each turbine in the wake')

                    x = ffor.x_vec
                    y = ffor.y_vec
                    # X, Y = np.meshgrid(x, y)
                    X, Y = ffor.x_mat, ffor.y_mat
                    ref_rotor_x_emitting = (meta.hub_x[0] + np.cos(np.linspace(-pi, pi))) / 2.
                    ref_rotor_y_emitting = (meta.hub_y + np.sin(np.linspace(-pi, pi))) / 2.
                    for i_z in np.arange(0, 3):
                        # for i_z in np.arange(0, meta.nz):
                        ref_rotor_x_concerned = (meta.hub_x[i_z] + np.cos(np.linspace(-pi, pi))) / 2.
                        ref_rotor_y_concerned = (meta.hub_y + np.sin(np.linspace(-pi, pi))) / 2.
                        for i_t in np.arange(0, meta.nt, 4):
                            plt.cla()
                            plt.clf()
                            print 'i_t = ', i_t
                            if True:
                                plt.subplot(121)
                                CS1 = plt.contourf(X, Y, FFOR_result[:, :, i_z, i_t])#, np.linspace(0., 1., 20))
                                plt.xlabel('x'), plt.ylabel('y'), plt.title(
                                    'Axial WS FFoR for Turbine ' + str(meta.wtg_ind[i_z]))  # 7-iz
                                plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
                                plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
                                plt.legend()
                                plt.colorbar(CS1)
                                plt.draw()
                                plt.pause(0.0001)
                    plt.ioff()
        # Farm_p_out= Farm_p_out+out[str(meta.wtg_ind[0])][4] # based on power curve

        # /!\/!\ not put in commentary this  /!\/!\
        #"""
        # Total power
        Farm_p_out= Farm_p_out+out[str(meta.wtg_ind[0])][0] # based on BEM
        # Power by each turbine
        WT_p_out[iT]=out[str(meta.wtg_ind[0])][0]
        # Pitch and RPM
        """
        WT_pitch_out[iT,0]=aero.PITCH
        WT_pitch_out[iT,1]=aero.PITCH_opt
        WT_RPM_out[iT,0]=aero.RPM
        WT_RPM_out[iT,1]=aero.RPM_opt
        #"""
        Vel_out[iT]=out[str(meta.wtg_ind[0])][1]

        #PLOTTING
        """
        POWER_TURBINE=POWER_TURBINE+[out[str(meta.wtg_ind[0])][0]]
        VEL_plot=VEL_plot+[meta.mean_WS_DWM]
        RPM_plot=RPM_plot+[WT_RPM_out[iT,0]]
        PITCH_plot=PITCH_plot+[WT_pitch_out[iT,0]]
        #"""

        print '# -------------------------- # PROCESSING for iteration '+str(iT)+' ended # -------------------------- #'
        print '########################################################################################################'
        print '########################################################################################################'

    print '# -------------------------- # MAIN LOOP OVER TURBINE PROCESS ENDED # ------------------------------------ #'
    print '############################################################################################################'

    #
    #
    # print id0
    # print 'xind', xind
    # print 'wtp', WT_p_out[id0]
    # print 'pitch', WT_pitch_out[id0]
    # print 'omega', WT_RPM_out[id0]
    # print 'vel', Vel_out[id0]
    # print 'xind', xind[id0]
    """ Main Results Plot"""
    """
    plt.plot(range(WF.nWT),POWER_TURBINE)
    plt.title('Power Production for each Turbines'), plt.xlabel('Turbine Location'), plt.ylabel('Power (kW)')
    plt.show()

    plt.plot(range(WF.nWT), VEL_plot)
    plt.title('Velocity for each Turbines'), plt.xlabel('Turbine Location'), plt.ylabel('Velocity (m/s)')
    plt.show()

    plt.plot(range(WF.nWT), RPM_plot)
    plt.title('RPM for each Turbines'), plt.xlabel('Turbine Location'), plt.ylabel('RPM')
    plt.show()

    plt.plot(range(WF.nWT), PITCH_plot)
    plt.title('Pitch for each Turbines'), plt.xlabel('Turbine Location'), plt.ylabel('Pitch ()')
    plt.show()
    """
    print 'The farm production is: %4.2f kW, where each turbine is: %s' %(Farm_p_out,np.array_str(WT_p_out))
    print 'Vel_out:', Vel_out
    return Farm_p_out, WT_p_out[id0] ,WT_pitch_out[id0] ,WT_RPM_out[id0] ,Vel_out[id0], id0