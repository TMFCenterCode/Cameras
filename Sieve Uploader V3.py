from sys import exit
from glob import glob
from os import rename, system, path
from time import time, sleep
from random import random
import multiprocessing as mp
import asyncio

import aiohttp
import requests
import ffmpeg

SIEVE_API_URL = "https://api.sievedata.com/v1/"
SIEVE_PROJECT_NAME = "monitoring"
SIEVE_API_KEY = "FJplWaeLHndkh0V14xLdWt0gneA72V3XFQJ2Teu4aaU"
MAX_NUM_OF_BYTES = '1000000000' # this matches a number which has been set on sieves end. Right now set to 1GB

PATH_TO_CAMERAS = '\\\\nas920\\CameraVideo\\'

PATH_TO_CAMERA_VIDEO = '\\\\nas920\\CameraVideo\\'
PATH_TO_TEMP_VIDEO = PATH_TO_CAMERA_VIDEO+'TempVideo\\'

DEBUG = False

def upload_video(local_video_path, Name):
	"""Gets upload URL from Sieve, uploads local video to it, and returns a hosted URL"""
	signed_url_info = requests.post(
		SIEVE_API_URL + "create_local_upload_url",
		json={
			"file_name": Name,
		},
		headers={
			"X-API-Key": SIEVE_API_KEY,
				'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
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

async def SieveUnitTest(Session, File):
	Name = File.split('\\')[-1]
	if DEBUG: print('  Uploading:', Name)
	Mark = time()
	try:
		if path.isfile(File):
			hosted_url = upload_video(File, Name)
			if DEBUG: print('Upload complete in:', round(time()-Mark,2), 'seconds.')
			
			Mark2 = time()
			if DEBUG: print('  Processing:', Name)
			out = process_video(Session, Name, hosted_url)
			#out = process_video(session, url, x)
			print(' ',out['description'])
			if DEBUG: print('Processing complete in:', round(time()-Mark2,2), 'seconds.')
			print('  Total Exchange Duration:', round(time()-Mark,2), 'seconds.')
			if   'queuing' in out['description']:
				return 'Successfully Uploaded'
			elif 'exists'  in out['description']:
				return 'Successfully Uploaded'
			else:
				return 'Error'
		else:
			print('  This file was trash collected')
	except FileNotFoundError:
		print('  This file was trash collected')
	
		# if it was trash collected, its okay to ignore it.
	return 'Successfully Uploaded'
	
async def process_video(Session, video_name, video_url):
	async with Session.post(SIEVE_API_URL + "push_video",
				json={
					"project_name": SIEVE_PROJECT_NAME,
					"video_url": video_url,
					"video_name": video_name
				},
				headers={
					"X-API-Key": SIEVE_API_KEY,
					'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
				}
			) as response:
			#data = await response.text()
			data = await response
			return data


def GetFiles(Camera,l):
	FileList = []
	for File in glob(PATH_TO_TEMP_VIDEO+Camera+'*.mp4'):
		if not File in l:
			FileList.append(File)
	return FileList

def UploadHost(Session, Camera, l):
	MaxListLength = 300
	UnprocessedFiles = GetFiles(Camera,l)
	for File in UnprocessedFiles:
		print(Camera,'\t List:',len(l))
		try:
			#mp.Process(target=SieveUnitTest, args=(File,)).start()
			
			await SieveUnitTest(Session, File)
			Result = ''
			if Result ==  'Successfully Uploaded':
				l.insert(0,File)
			else:
				'Dont, I guess'
				
		except Exception as e:
			print('  UploadHost Error',e)
		if len(l) > MaxListLength:
			l = l[0:MaxListLength]
	return l 

async def Main():
	CameraDict = {}
	for CameraDir in glob(PATH_TO_CAMERAS+'Camera*\\'):
		Camera = CameraDir.split('\\')[-2]
		CameraDict[Camera] = []
	
	async with aiohttp.ClientSession() as Session:
		for Camera, l in CameraDict.items():
			CameraDict[Camera] = UploadHost(Session, Camera, l)
			#mp.Process(target=UploadHost, args=(Camera,Session)).start()
		#break
		



if __name__ == '__main__':
	#asyncio.run(Main())
	asyncio.get_event_loop().run_until_complete(Main())
	