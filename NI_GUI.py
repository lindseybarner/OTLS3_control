import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo

import numpy
import math
import hardware.ni_AGY as ni


# set up to NI

# VOLTAGE PARAMETERS
daq_rate = 1e5  # Hz
daq_name = '6738'  # PCIe card name
daq_board = 'Dev1'
daq_num_channels = 32  # AO channels
n2c = {'xgalvo': 29,
       'ygalvo': 30,
       'etl': 31}

# ############## CONNECT NIDAQ ###############

ao = ni.Analog_Out(num_channels=daq_num_channels,
                   rate=daq_rate,
                   daq_type=daq_name,
                   board_name=daq_board,
                   verbose=False)


# root window
root = tk.Tk()
# root.geometry("300x150")
root.resizable(False, False)
root.title('Voltage control')

# store voltage values
Xmax = tk.StringVar()
Xmin = tk.StringVar()
Xpp = tk.StringVar()

Ymax = tk.StringVar()
Ymin = tk.StringVar()
Ypp = tk.StringVar()

Econst = tk.StringVar()


def update_voltages():
    """ callback when the login button clicked
    """

    freq = 100  # Hz
    duration = 1.0  # seconds
    period_pix = ao.s2p(1/freq)
    nFrames = freq * duration

    try:
        Xamp = float(Xpp.get()) / 2
        Xoff = (float(Xmax.get()) + float(Xmin.get())) / 2

        Yamp = float(Ypp.get()) / 2
        Yoff = (float(Ymax.get()) + float(Ymin.get())) / 2

        Eamp = 0.0
        Eoff = float(Econst.get())

    except ValueError:
        msg = f'Invalid voltages, please try again'
        showinfo(
            title='Error',
            message=msg
        )
        return

    voltages = []

    for sl in range(int(nFrames)):  # add buffer for scan rampup

        v = numpy.zeros((period_pix, daq_num_channels), 'float64')

        # X galvo
        time = numpy.linspace(0, 2*math.pi, period_pix)
        v[:, n2c['xgalvo']] = 2*Xamp/math.pi*numpy.sin(time)+Xoff

        # Y galvo
        time = numpy.linspace(0, 2*math.pi, period_pix)
        v[:, n2c['ygalvo']] = 2*Yamp/math.pi*numpy.sin(time)+Yoff

        # ETL
        time = numpy.linspace(0, 2*math.pi, period_pix)
        v[:, n2c['etl']] = 2*Eamp/math.pi*numpy.sin(time)+Eoff

        voltages.append(v)

    voltages = numpy.concatenate(voltages, axis=0)

    # Check final voltages for sanity
    # Assert that voltages are safe
    assert numpy.max(voltages[:, n2c['xgalvo']]) <= 5.0
    assert numpy.min(voltages[:, n2c['xgalvo']]) >= -5.0
    # assert numpy.max(voltages[:,n2c['ygalvo']]) <= 5.0
    # assert numpy.min(voltages[:,n2c['ygalvo']]) >= -5.0
    # assert numpy.max(voltages[:,n2c['etl']]) <= 5.0
    # assert numpy.min(voltages[:,n2c['etl']]) >= 0.0

    print('potato')
    return voltages


# Main frame
main_frame = ttk.Frame(root)
main_frame.pack(padx=10, pady=10, fill='x', expand=True)


# Xmax
Xmax_label = ttk.Label(main_frame, text="Xmax:")
Xmax_label.pack(fill='x', expand=True)

Xmax_entry = ttk.Entry(main_frame, textvariable=Xmax)
Xmax_entry.pack(fill='x', expand=True)
Xmax_entry.insert(0, "0.0")
# Xmax_entry.focus()

# Xmin
Xmin_label = ttk.Label(main_frame, text="Xmin:")
Xmin_label.pack(fill='x', expand=True)

Xmin_entry = ttk.Entry(main_frame, textvariable=Xmin)
Xmin_entry.pack(fill='x', expand=True)
Xmin_entry.insert(0, "0.0")


# Xpp
Xpp_label = ttk.Label(main_frame, text="Xpp:")
Xpp_label.pack(fill='x', expand=True)

Xpp_entry = ttk.Entry(main_frame, textvariable=Xpp)
Xpp_entry.pack(fill='x', expand=True)
Xpp_entry.insert(0, "0.0")


# Ymax
Ymax_label = ttk.Label(main_frame, text="Ymax:")
Ymax_label.pack(fill='x', expand=True)

Ymax_entry = ttk.Entry(main_frame, textvariable=Ymax)
Ymax_entry.pack(fill='x', expand=True)
Ymax_entry.insert(0, "0.0")
# Xmax_entry.focus()

# Ymin
Ymin_label = ttk.Label(main_frame, text="Ymin:")
Ymin_label.pack(fill='x', expand=True)

Ymin_entry = ttk.Entry(main_frame, textvariable=Ymin)
Ymin_entry.pack(fill='x', expand=True)
Ymin_entry.insert(0, "0.0")

# Ypp
Ypp_label = ttk.Label(main_frame, text="Ypp:")
Ypp_label.pack(fill='x', expand=True)

Ypp_entry = ttk.Entry(main_frame, textvariable=Ypp)
Ypp_entry.pack(fill='x', expand=True)
Ypp_entry.insert(0, "0.0")

# Econst
Econst_label = ttk.Label(main_frame, text="Econst:")
Econst_label.pack(fill='x', expand=True)

Econst_entry = ttk.Entry(main_frame, textvariable=Econst)
Econst_entry.pack(fill='x', expand=True)
Econst_entry.insert(0, "0.0")

# update button
update_button = ttk.Button(main_frame, text="Update voltages",
                           command=update_voltages)
update_button.pack(fill='x', expand=True, pady=10)


def playV():
    print('Send', Xmax.get())
    ao.play_voltages(voltages, block=False)

    root.after(1000, playV)


voltages = update_voltages()
playV()

root.mainloop()
