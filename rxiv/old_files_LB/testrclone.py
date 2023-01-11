import subprocess
import sys
import time
import os
import rclone.rclone as rclone
drive='Y'
fname='mouse_prostate_mAb.594_8.8.19'
rclone = rclone.rcloneUpload(drive, fname, 'lsm')
rclone.start()