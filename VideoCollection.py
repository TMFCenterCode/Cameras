from datetime import datetime, timedelta
from glob import glob
from os import system, rename, path, remove
from sys import exit
from time import time
import multiprocessing as mp

import ffmpeg

PATH_TO_CAMERA_VIDEO = '\\\\nas920\\CameraVideo\\'
PATH_TO_TEMP_VIDEO = PATH_TO_CAMERA_VIDEO+'TempVideo\\'
RTSP_USER = 'admin'
RTSP_PASS = 'TMFeyeofsauron'
RTSP_PORT = ':554'
RTSP ='rtsp://'+RTSP_USER+':'+RTSP_PASS+'@'

CamIPDict = \
{
	'Camera1':'192.168.1.248',
	'Camera2':'192.168.1.249',
	'Camera3':'192.168.1.247',
}

def SaveVideo(Camera,CameraIP):
	while True:
		FPS = 15
		VIDEO_LENGTH = 10
		vframes = int(FPS*VIDEO_LENGTH)
		
		
		Date = datetime.strftime(datetime.now(),'%Y-%m-%d')
		TimeCode = datetime.strftime(datetime.now(),'%H-%M-')
		TimeCodeSeconds = datetime.strftime(datetime.now(),'%S')[0]+'0'
		
		OutFile = PATH_TO_TEMP_VIDEO+'%s %s %s%s %ss.mp4'%(Camera,Date,TimeCode,TimeCodeSeconds,VIDEO_LENGTH)
		if not path.isfile(OutFile):
			Mark = time()
			RTSPInfo = RTSP+CameraIP+RTSP_PORT
			Command = \
			(
				'ffmpeg -i '+RTSPInfo
				+' -pattern_type none '
				+' -hide_banner -loglevel error '
				+' -r '+str(FPS)
				+' -vframes '+str(vframes)
				+' "'+OutFile+'"'
			)
			system(Command)
			print(OutFile)
			print('Time Elapsed:', round(time()-Mark,2))
			
			TrashCollectOldFiles(Camera,VIDEO_LENGTH)

def TrashCollectOldFiles(Camera,VIDEO_LENGTH):
	for OldFile in glob(PATH_TO_TEMP_VIDEO+Camera+' *.mp4'):
		OldFileName = OldFile.split('\\')[-1]
		OldFileDateTime = datetime.strptime(OldFileName,Camera+' %Y-%m-%d %H-%M-%S '+str(VIDEO_LENGTH)+'s.mp4')
		if OldFileDateTime < datetime.now()-timedelta(minutes=2):
			try:
				remove(OldFile)
			except PermissionError:
				pass

def MultiTime():
	for Camera,CameraIP in CamIPDict.items():
		mp.Process(target=SaveVideo, args=(Camera,CameraIP)).start()
	

if __name__ == '__main__':
	MultiTime()