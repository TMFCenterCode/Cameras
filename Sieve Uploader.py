from sys import exit
from glob import glob
from os import system, rename, path, remove
from time import time, sleep
from random import random

import requests
import ffmpeg

SIEVE_API_URL = "https://api.sievedata.com/v1/"
SIEVE_PROJECT_NAME = "monitoring"
SIEVE_API_KEY = "FJplWaeLHndkh0V14xLdWt0gneA72V3XFQJ2Teu4aaU"
MAX_NUM_OF_BYTES = '1000000000' # this matches a number which has been set on sieves end. Right now set to 1GB

PATH_TO_CAMERA_VIDEO = '\\\\nas920\\CameraVideo\\'
PATH_TO_UNTRUNC = PATH_TO_CAMERA_VIDEO+'untrunc\\'
PATH_TO_HEALTHY_VIDEO = PATH_TO_UNTRUNC+'HealthyVideo.mp4'

PATH_TO_CAMERAS = '\\\\nas920\\CameraVideo\\'


DEBUG = True

def upload_video(local_video_path, Name):
	"""Gets upload URL from Sieve, uploads local video to it, and returns a hosted URL"""
	signed_url_info = requests.post(
		SIEVE_API_URL + "create_local_upload_url",
		json={
			"file_name": Name,
		},
		headers={
			"X-API-Key": SIEVE_API_KEY
		}
	).json()

	upload_url = signed_url_info["upload_url"]
	get_url = signed_url_info["get_url"]

	with open(local_video_path, "rb") as f:
		requests.put(
			upload_url,
			data=f,
			headers = {
				'x-goog-content-length-range': '0,'+MAX_NUM_OF_BYTES
			}
		)

	return get_url

def process_video(video_name, video_url):
	"""Sends video URL to Sieve for processing, and returns the result"""
	return requests.post(
		SIEVE_API_URL + "push_video",
		json={
			"project_name": SIEVE_PROJECT_NAME,
			"video_url": video_url,
			"video_name": video_name
		},
		headers={
			"X-API-Key": SIEVE_API_KEY
		}
	).json()

# ################################################ #
####################################################
# ################################################ #

def GetFilePath():
	l = []
	for CameraPath in glob(PATH_TO_CAMERAS+'Camera*\\'):
		Camera = CameraPath.split('\\')[-2]
		for DatePath in glob(CameraPath+'*\\001\\dav\\'):
			Date = DatePath.split('\\')[-4]
			for HourPath in glob(DatePath+'*\\*0@0*.mp4'):
				Hour = HourPath.split('\\')[-1]
				HourDir = HourPath.replace(Hour,'')
				d = {'HourPath':HourPath,'HourDir':HourDir,'Camera':Camera,'Date':Date,'Hour':Hour}
				d = GenOutPathName(d)
				l.append(d)
	return l

def GenOutPathName(d):
	Hour = d['Hour']	
	for k,v in {'[R][0@0][0]':'',
				'[M][0@0][0]':'',
				'.00-':'-',
				'.00.':'.',
				'.59-':'-',
				'.59.':'.',}.items():
		Hour = Hour.replace(k,v)
	d['OutName'] = d['HourDir']+d['Camera']+' '+d['Date']+' '+Hour
	return d

def SieveUnitTest(FileDict):
	ConvertFileName(FileDict)
	
	# This is the fake name we use during set up
	Name = 'TEST_'+str(random())+'_'+FileDict['OutName'].replace(FileDict['HourDir'],'')
	
	# This is the actual name
	#Name = FileDict['OutName'].replace(FileDict['HourDir'],'')
	
	if DEBUG: print('Uploading:', Name)
	Mark = time()
	hosted_url = upload_video(FileDict['OutName'].replace('.mp4','_clipped.mp4'),Name)
	if DEBUG: print('Upload complete in:', round(time()-Mark,2), 'seconds.')
	
	Mark2 = time()
	if DEBUG: print('Processing:', Name)
	out = process_video(Name, hosted_url)
	if DEBUG: print('Processing complete in:', round(time()-Mark2,2), 'seconds.')
	print('Total Exchange Duration:', round(time()-Mark,2), 'seconds.')
	print(out)


def ConvertFileName(FileDict):
	source = FileDict['HourPath']
	dest = FileDict['OutName']
	if DEBUG: print('Beginning FFMPEG...')
	(
		ffmpeg
		.input(source)
		.filter('fps', fps=3, round='up')
		.output(dest.replace('.mp4','_clipped.mp4'))
		.run()
	)
	if DEBUG: print('FFMPEG Complete.')
	rename(source, dest)
	
def Untrunc(TruncFile):

	# .\untrunc.exe \\nas920\CameraVideo\12.00-12.30.mp4 \\nas920\CameraVideo\13.30.00-13.30.00[R][0@0][0].mp4_

	mark = time()
	print('Attemping Untrunc on:', TruncFile)
	
	#GoodFile = PATH_TO_CAMERA_VIDEO+'12.00-12.30.mp4'
	
	Source = TruncFile+'_fixed.mp4'
	if path.isfile(Source):
		remove(Source)
		
	Command = \
	(
		PATH_TO_UNTRUNC+'untrunc.exe'
		+' '
		+PATH_TO_HEALTHY_VIDEO
		+' '
		+TruncFile
	)
	system(Command)	

if __name__ == '__main__':
	while True:
		try:
			print('\nChecking for unprocessed files...')
			UnprocessedFiles = GetFilePath()
		except Exception as e:
			print('UnprocessedFiles Error:', e)
			
		if len(UnprocessedFiles) != 0:
			print('Unprocessed Files List:')
		for FileDict in UnprocessedFiles:
			print('\t',FileDict['OutName'])
		
		for FileDict in UnprocessedFiles:
			try:
				print('Beginning Process for',FileDict['OutName'])
				SieveUnitTest(FileDict)
				if DEBUG: print('\tUnit Test Complete')
			except Exception as e:
				print('SieveUnitTest Error:', e)
				Untrunc(FileDict['OutName'])
				
				
				
				
		sleep(60)