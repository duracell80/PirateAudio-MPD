import signal, os, re, sys, time, subprocess

ls_playlists        = subprocess.check_output("mpc lsplaylists", stderr=subprocess.STDOUT, shell=True)
playlists           = ls_playlists.split()
print(playlists[1])