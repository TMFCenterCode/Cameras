from datetime import datetime
from glob import glob
from os import system, rename, path, remove
from sys import exit
from time import time

import ffmpeg


PATH_TO_CAMERA_VIDEO = '\\\\nas920\\CameraVideo\\'
PATH_TO_TEMP_VIDEO = PATH_TO_CAMERA_VIDEO+'Temp Video\\'
PATH_TO_UNTRUNC = PATH_TO_CAMERA_VIDEO+'untrunc\\'
PATH_TO_HEALTHY_VIDEO = PATH_TO_CAMERA_VIDEO+'HealthyVideo.mp4'

Date = datetime.strftime(datetime.now(),'%Y-%m-%d')
Hour = datetime.strftime(datetime.now(),'%H')
GlobPath = PATH_TO_CAMERA_VIDEO+'*\\'+Date+'\\001\\dav\\'+Hour+'\\*.mp4_'



def Untrunc():
	for TruncFile in glob(GlobPath):
		mark = time()
		print('Attemping on:', TruncFile)
		
		#GoodFile = PATH_TO_CAMERA_VIDEO+'12.00-12.30.mp4'
		
		Source = TruncFile+'_fixed.mp4'
		if path.isfile(Source):
			remove(Source)
			
		Command = \
		(
			PATH_TO_UNTRUNC+'untrunc.exe '
			+PATH_TO_HEALTHY_VIDEO
			+' '
			+TruncFile
		)
		system(Command)
		
		'''
		while True:
			if path.isfile(Source):
				break
			sleep(1)
		'''
		
		Dest = PATH_TO_TEMP_VIDEO+Source.split('\\')[-1].replace('.mp4__fixed.mp4','.mp4')
		if path.isfile(Dest):
			remove(Dest)
		
		print('\ntime elapsed before FFmpeg:', round(time()-mark,2), '\n')
		(
			ffmpeg
			.input(Source)
			.filter('fps', fps=3, round='up')
			.output(Dest)
			.run()
		)
		
		#rename(Source, Dest)
		print('\ntime elapsed:', round(time()-mark,2))
		exit()
		
if __name__ == '__main__':
	Untrunc()