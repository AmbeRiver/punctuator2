#!/usr/bin/env python3

import sys
import asyncio
import pathlib
import websockets
import concurrent.futures
import resotrepunnc
import words2number
import json

pool = concurrent.futures.ThreadPoolExecutor()
loop = asyncio.get_event_loop()

def process_chunk(message):
    if message is not None:
        transcript = words2number.Transcript()
        transcript.readInput(message)
        inputstring = ""
        if transcript.isValid():
            transcript.words2num()
            inputstring=transcript.getResult()
        else:
            return "punctuator error"
        pun = resotrepunnc.PunctuateRestore()
        punstring = pun.restore("Demo-Europarl-EN.pcl","0",inputstring)
        print("final string: "+punstring)
        return punstring, True

async def recognize(websocket, path):
    rec = KaldiRecognizer(model);
    while True:
        message = await websocket.recv()
        response, stop = await loop.run_in_executor(pool, process_chunk, rec, message)
           
        await websocket.send(response)
        if stop: break

start_server = websockets.serve(
    recognize, '0.0.0.0', 2900)

loop.run_until_complete(start_server)
loop.run_forever()
