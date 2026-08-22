import os
from BRAVOClient import BRAVOPlatformRequest

requester = BRAVOPlatformRequest("", "https://bravo.rc.ufl.edu")

Participants = requester.QueryParticipants()
Participant = [participant for participant in Participants if participant["Name"] == "RCP_UF_01"][0]

Recordings = requester.QueryTimeSeriesAnalysis(Participant["Id"])
Recording = Recordings[0]
Data = requester.QueryTimeSeriesAnalysis(Participant["Id"], Recording["Id"])
