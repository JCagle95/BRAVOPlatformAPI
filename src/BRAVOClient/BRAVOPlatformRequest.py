import requests
import json
import os
import pickle as pkl
import datetime
import numpy as np 
import zstandard as zstd

"""BRAVO platform client helpers.

This module provides a Python interface for the Brain Recording Analysis and
Visualization Online (BRAVO) API. It wraps common REST endpoints for participant
management, study organization, time-series queries, survey handling, and data
upload workflows.
"""

DefaultConfigurations = {
    "TimeSeriesRecording": {
        "StandardFilter": {
            "name": "Standard Bandpass Filter",
            "description": "",
            "options": ["No Filter", "Butterworth 1-100Hz"],
            "value": "No Filter"
        },
        "NotchFilter": {
            "name": "Powerline Noise Notch Filter",
            "description": "",
            "options": ["No Filter", "Notch 55-65Hz", "Notch 45-55Hz"],
            "value": "No Filter"
        },
        "WienerFilter": {
            "name": "Wiener Filter for Artifact Removals",
            "description": "",
            "options": ["No Filter", "Use Wiener Filter"],
            "value": "No Filter"
        },
        "CardiacFilter": {
            "name": "Cardiac Filter for EKG Removals",
            "description": "",
            "options": ["No Filter", "Use Adaptive Template Matching"],
            "value": "No Filter"
        },
        "SpectrogramMethod": {
            "name": "Time-Frequency Analysis Algorithm",
            "description": "",
            "options": ["Welch's Periodogram", "Short-time Fourier Transform", "Wavelet",
                        "Autoregressive Model (Yule-Walker)"],
            "value": "Welch's Periodogram"
        },
        "BaselineCorrection": {
            "name": "Baseline Correlation for Time-Frequency Analysis",
            "description": "",
            "options": ["No Correction"],
            "value": "No Correction"
        },
        "Normalization": {
            "name": "Normalization for Time-Frequency Analysis",
            "description": "",
            "options": ["No Normalization", "1/f PSD Trend Removal"],
            "value": "No Normalization"
        },
    },
    "PowerSpectralDensity": {
        "PSDMethod": {
            "name": "Power Spectrum Estimation Algorithm",
            "description": "",
            "options": ["Estimated Medtronic PSD", "Welch's Periodogram", "Autoregressive Model (Yule-Walker)",
                        "Short-time Fourier Transform"],
            "value": "Welch's Periodogram"
        },
        "MonopolarEstimation": {
            "name": "Monopolar Estimation Algorithm",
            "description": "",
            "options": ["No Estimation", "DETEC Algorithm (Strelow et. al., 2022)"],
            "value": "No Estimation"
        },
    }
}


class BRAVOPlatformRequest:
    """Client for the BRAVO platform API.

    The client authenticates with the configured BRAVO server and exposes
    convenience methods for querying participant information, studies,
    neural recordings, surveys, and uploaded data.

    :param api_key: Secure API key used to authenticate requests.
    :type api_key: str
    :param server: Base URL for the BRAVO server.
    :type server: str
    :raises Exception: If the BRAVO profile request fails during initialization.
    """

    def __init__(self, api_key, server="http://localhost:27286"):
        """Initialize the BRAVO client and fetch the authenticated user profile.

        :param api_key: Secure API key used to authenticate requests.
        :type api_key: str
        :param server: Base URL for the BRAVO server.
        :type server: str
        :raises Exception: If the BRAVO server rejects the API key or profile request.
        """
        self.__Server = server
        self.__request = requests.Session()
        self.__API_Key = api_key

        self.User = self.GetUserInfo()

    def query(self, url, data=None, files=None, content_type="application/json"):
        """Send an authenticated POST request to a BRAVO API endpoint.

        :param url: Relative URL path to the BRAVO API endpoint.
        :type url: str
        :param data: JSON payload to send with the request.
        :type data: dict or None
        :param files: Multipart upload payload when sending a file.
        :type files: dict or None
        :param content_type: Request content type to set on the outgoing header.
        :type content_type: str or None
        :return: Response object returned by the BRAVO endpoint.
        :rtype: requests.Response
        """
        if not content_type:
            Headers = {"X-Secure-API-Key": self.__API_Key}
        else:
            Headers = {"Content-Type": content_type, "X-Secure-API-Key": self.__API_Key}

        if data:
            return self.__request.post(self.__Server + url,
                                       json.dumps(data) if content_type else data,
                                       headers=Headers)
        elif files:
            return self.__request.post(self.__Server + url,
                                       files=files,
                                       headers=Headers)
        else:
            return self.__request.post(self.__Server + url,
                                       headers=Headers)

    def GetUserInfo(self):
        """Return the authenticated user's profile from the BRAVO server.

        :return: User profile payload returned by the BRAVO API.
        :rtype: dict
        :raises Exception: If the BRAVO request returns a network or authorization error.
        """
        response = self.query("/api/queryProfile")
        if response.status_code == 200:
            payload = response.json()
            self.User = payload
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryParticipants(self):
        """List all participants visible to the authenticated user.

        :return: List of participant records from the BRAVO platform.
        :rtype: list[dict]
        :raises Exception: If the server returns an error response.
        """
        response = self.query("/api/queryParticipants")
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryParticipantInformation(self, participant_uid):
        """Fetch metadata for a specific participant.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :return: Participant information payload.
        :rtype: dict
        :raises Exception: If the participant lookup fails.
        """
        form = {"ParticipantId": participant_uid}
        response = self.query("/api/queryParticipantInformation", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def UpdateParticipantInformation(self, participant_uid, info):
        """Update information for a participant record.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :param info: Dictionary of fields to update.
        :type info: dict
        :return: Server response payload.
        :rtype: dict
        :raises Exception: If the update request fails.
        """
        form = {"ParticipantId": participant_uid}
        form = {**form, **info}

        response = self.query("/api/updateParticipantInformation", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def ListAllStudies(self):
        """List all studies available in the BRAVO platform.

        :return: Study metadata payload.
        :rtype: dict or list
        :raises Exception: If the request fails on the server.
        """
        form = {"RequestType": "GetStudies"}
        response = self.query("/api/manageStudyInformation", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def CreateNewStudy(self, study_name):
        """Create a new study in the BRAVO system.

        :param study_name: Name to assign to the new study.
        :type study_name: str
        :return: Server response payload for the created study.
        :rtype: dict
        :raises Exception: If the study creation request fails.
        """
        form = {"RequestType": "CreateStudy", "StudyName": study_name}
        response = self.query("/api/manageStudyInformation", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def AddParticipantToStudy(self, study_id, participant_uid):
        """Add a participant to an existing study.

        :param study_id: Identifier for the target study.
        :type study_id: str
        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :return: ``True`` when the participant is added successfully.
        :rtype: bool
        :raises Exception: If the assignment request fails.
        """
        form = {"RequestType": "AddParticipant", "StudyId": study_id, "ParticipantId": participant_uid}
        response = self.query("/api/manageStudyInformation", data=form)
        if response.status_code == 200:
            return True
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def RemoveParticipantFromStudy(self, study_id, participant_uid):
        """Remove a participant from an existing study.

        :param study_id: Identifier for the target study.
        :type study_id: str
        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :return: ``True`` when the removal succeeds.
        :rtype: bool
        :raises Exception: If the removal request fails.
        """
        form = {"RequestType": "RemoveParticipant", "StudyId": study_id, "ParticipantId": participant_uid}
        response = self.query("/api/manageStudyInformation", data=form)
        if response.status_code == 200:
            return True
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryTherapyHistory(self, participant_uid):
        """Return therapy history for a participant.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :return: Therapy history payload returned by the BRAVO platform.
        :rtype: dict or list
        :raises Exception: If the server response indicates an error.
        """
        form = {"ParticipantId": participant_uid}
        response = self.query("/api/queryTherapyHistory", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryTherapeuticEffectAnalysis(self, participant_uid, analysis_uid=None, config=None):
        """Query therapeutic-effect analysis records or a specific analysis payload.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :param analysis_uid: Optional analysis identifier to request a specific result.
        :type analysis_uid: str or None
        :param config: Optional processing configuration dictionary.
        :type config: dict or None
        :return: Overview data or a specific analysis result.
        :rtype: dict
        :raises Exception: If the request fails.
        """
        form = {"ParticipantId": participant_uid, "RequestType": "Overview"}
        if analysis_uid:
            form["RequestType"] = "RequestData"
            form["AnalysisId"] = analysis_uid
            form["ActiveChannels"] = "RequestAllChannel"

        if config:
            form["ProcessingConfiguration"] = config

        response = self.query("/api/queryTherapeuticEffectAnalysis", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def SetRecordingTimeShift(self, participant_uid, recording_uid, shift=0):
        """Set the time alignment shift for a recorded signal.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :param recording_uid: Unique identifier for the recording.
        :type recording_uid: str
        :param shift: Time-alignment offset to apply to the recording.
        :type shift: int or float
        :return: ``True`` if the shift is accepted.
        :rtype: bool
        :raises Exception: If the update request fails.
        """
        form = {"RequestType": "Recording", "ParticipantId": participant_uid, "RecordingId": recording_uid, "Alignment": shift}
        response = self.query("/api/setRecordingTimeShift", data=form)
        if response.status_code == 200:
            return True
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryNeuralActivitySnapshot(self, participant_uid, config=None):
        """Return a snapshot of participant neural activity.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :param config: Optional processing configuration to apply.
        :type config: dict or None
        :return: Snapshot payload returned by the platform.
        :rtype: dict
        :raises Exception: If the BRAVO endpoint returns an error.
        """
        form = {"ParticipantId": participant_uid, "RequestType": "RequestAll"}
        if config:
            form["ProcessingConfiguration"] = config

        response = self.query("/api/queryNeuralActivitySnapshot", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryTimeSeriesAnalysis(self, participant_uid, recording_uid=None, config=None,
                                refresh=False):
        """Fetch time-series analysis metadata or compressed time-series data.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :param recording_uid: Optional recording identifier to fetch a single trace.
        :type recording_uid: str or None
        :param config: Optional processing configuration dictionary.
        :type config: dict or None
        :param refresh: If ``True``, clear cached results and reload data.
        :type refresh: bool
        :return: Time-series overview or recording payload, including decoded numpy data for single-record requests.
        :rtype: dict
        :raises Exception: If the BRAVO API request fails.
        """
        form = {"ParticipantId": participant_uid, "RequestType": "Overview"}
        if recording_uid:
            form["RequestType"] = "RequestData"
            form["RecordingId"] = recording_uid
            form["ActiveChannels"] = "RequestAllChannel"

        if refresh:
            form["RequestType"] = "DeleteCache"

        if config:
            form["ProcessingConfiguration"] = config

        response = self.query("/api/v2/queryTimeseriesAnalysis", data=form)
        if response.status_code == 200:
            if refresh:
                return self.QueryTimeSeriesAnalysis(participant_uid, recording_uid, config)

            if recording_uid:
                metadata = response.headers.get("X-Timeseries-Metadata")
                payload = json.loads(metadata)
                payload["Data"] = zstd.decompress(response.content)
                payload["Data"] = np.frombuffer(payload["Data"], dtype=np.float64).reshape(payload["DataShape"])
                return payload
            else:
                payload = response.json()
                return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryChronicNeuralActivity(self, participant_uid, refresh=False):
        """Return chronic neural activity records for a participant.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :param refresh: If ``True``, clear cached results and reload them.
        :type refresh: bool
        :return: Chronic neural activity payload.
        :rtype: dict or list
        :raises Exception: If the request fails.
        """
        form = {"ParticipantId": participant_uid, "RequestType": "RequestAll"}
        if refresh:
            form["RequestType"] = "DeleteCache"

        response = self.query("/api/queryChronicNeuralActivity", data=form)
        if response.status_code == 200:
            if refresh:
                return self.QueryChronicNeuralActivity(participant_uid)

            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryChronicTimeline(self, participant_uid):
        """Query the chronic timeline for a participant.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :return: Timeline payload for chronic data.
        :rtype: dict or list
        :raises Exception: If the server response indicates an error.
        """
        form = {"ParticipantId": participant_uid, "RequestType": "RequestAll"}
        response = self.query("/api/queryChronicTimeline", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryRawTimeseries(self, participant_uid, recording_uid=None):
        """Fetch raw time-series data for one participant or specific recording.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :param recording_uid: Optional recording identifier for a single dataset.
        :type recording_uid: str or None
        :return: Raw timeseries metadata or payload.
        :rtype: dict
        :raises Exception: If the query fails.
        """
        form = {"ParticipantId": participant_uid, "RequestType": "Overview"}
        if recording_uid:
            form["RequestType"] = "RawTimeseries"
            form["RecordingId"] = recording_uid

        response = self.query("/api/queryRawTimeseries", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QuerySurveyForms(self, form_link=None, version=None):
        """Query survey forms, optionally selecting a specific form version.

        :param form_link: Optional survey form link identifier.
        :type form_link: str or None
        :param version: Optional version number to request for a specific form.
        :type version: str or None
        :return: Survey form metadata from the BRAVO platform.
        :rtype: dict or list
        :raises Exception: If the survey query fails.
        """
        form = {"RequestType": "RequestAll"}
        if form_link:
            form["RequestType"] = "RequestForm"
            form["FormLink"] = form_link
            if version:
                form["VersionRel"] = version

        response = self.query("/api/querySurveyForms", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def CreateSurveyForm(self, institute, form_name):
        """Create a new survey form definition.

        :param institute: Institution or organization creating the form.
        :type institute: str
        :param form_name: Name of the survey form.
        :type form_name: str
        :return: Server response for the form creation request.
        :rtype: dict
        :raises Exception: If form creation fails.
        """
        form = {"RequestType": "Create", "Institute": institute, "FormName": form_name,
                "FormType": "API-Generated Form", "FormContent": []}
        response = self.query("/api/setSurveyForms", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def DeleteSurveyForm(self, form_uid):
        """Delete a survey form by identifier.

        :param form_uid: Unique identifier of the survey form.
        :type form_uid: str
        :return: ``True`` when the form is successfully deleted.
        :rtype: bool
        :raises Exception: If the deletion request fails.
        """
        form = {"FormId": form_uid}

        response = self.query("/api/deleteSurveyForms", data=form)
        if response.status_code == 200:
            return True
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def UpdateSurveyForm(self, form_link, content):
        """Update an existing survey form definition.

        :param form_link: Identifier or link of the form to update.
        :type form_link: str
        :param content: New survey form content payload.
        :type content: list or dict
        :return: Server response from the update operation.
        :rtype: dict
        :raises Exception: If the operation fails.
        """
        form = {"RequestType": "Create", "FormLink": form_link, "FormContent": content}
        response = self.query("/api/setSurveyForms", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def SubmitSurveyResponse(self, form_uid, version, responder_code, result={}, date=None):
        """Submit a survey response for a participant.

        :param form_uid: Unique identifier of the survey form.
        :type form_uid: str
        :param version: Version of the survey form.
        :type version: str or int
        :param responder_code: Passcode or responder identifier.
        :type responder_code: str
        :param result: Survey answer payload to submit.
        :type result: dict
        :param date: Optional submission timestamp in Unix seconds.
        :type date: float or None
        :return: Server response for the submitted survey response.
        :rtype: dict
        :raises Exception: If the submission request fails.
        """
        form = {"RequestType": "SubmitForm", "FormId": form_uid, "Version": version, "Passcode": responder_code,
                "FormResults": result}
        if not date:
            form["Date"] = datetime.datetime.now(datetime.timezone.utc).timestamp()
        else:
            form["Date"] = date

        response = self.query("/api/querySurveyForms", data=form)
        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QuerySurveyResponse(self, participant_uid, form_uid=None):
        """Get survey responses for a participant, optionally filtering by form.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :param form_uid: Optional form identifier used to filter responses.
        :type form_uid: str or None
        :return: Participant survey response payload.
        :rtype: dict or list
        :raises Exception: If the query fails.
        """
        form = {"ParticipantId": participant_uid, "RequestType": "RequestAll"}
        if form_uid:
            form["RequestType"] = "RequestRecords"
            form["FormId"] = form_uid
        response = self.query("/api/queryParticipantSurveyRecords", data=form)

        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def QueryEvents(self, participant_uid, data=False):
        """Query participant events, optionally requesting event data details.

        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :param data: If ``True``, include full data for each event record.
        :type data: bool
        :return: Event records for the participant.
        :rtype: dict or list
        :raises Exception: If the event request fails.
        """
        form = {"ParticipantId": participant_uid, "RequestType": "RequestAll"}
        if data:
            form["RequestType"] = "RequestData"
        response = self.query("/api/queryParticipantEvents", data=form)

        if response.status_code == 200:
            payload = response.json()
            return payload
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def DeleteData(self, recording_uid, participant=None):
        """Delete a recording from the BRAVO platform.

        :param recording_uid: Unique identifier of the recording to delete.
        :type recording_uid: str
        :param participant: Optional participant object containing uid and study metadata.
        :type participant: dict or None
        :return: ``True`` when the delete request succeeds.
        :rtype: bool
        :raises Exception: If the server returns a failure response.
        """
        participantObj = participant if participant else self.__ActiveParticipant
        data = {"participant": participantObj["uid"], "study": participantObj["study"], "recording_uid": recording_uid}
        response = self.query("/api/deleteData", data)
        if response.status_code == 200:
            return True
        elif response.status_code == 301:
            return True
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def RequestAnalysisPipeline(self, request_type, participant_uid):
        """Request a pipeline or analysis workflow for a participant.

        :param request_type: Name or type of analysis pipeline to request.
        :type request_type: str
        :param participant_uid: Unique identifier for the participant.
        :type participant_uid: str
        :return: Response payload for the analysis pipeline request.
        :rtype: dict or bool
        :raises Exception: If the server reports an error.
        """
        data = {"RequestType": request_type, "AnalysisName": request_type, "ParticipantId": participant_uid}
        response = self.query("/api/queryAnalysisPipeline", data)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 301:
            return True
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def RequestAIPrediction(self, request_type, data):
        """Send a request to a BRAVO AI prediction endpoint.

        :param request_type: Type of AI prediction or analysis to invoke.
        :type request_type: str
        :param data: Input payload used by the prediction model.
        :type data: dict or list
        :return: AI prediction response returned by the server.
        :rtype: dict or bool
        :raises Exception: If the prediction request fails.
        """
        data = {"RequestType": request_type, "AnalysisName": request_type, "Data": data}
        response = self.query("/api/requestAIPrediction", data)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 301:
            return True
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def UploadMedtronicJSON(self, participant, file, metadata={"device_location": "", "infer_from_device": True}):
        """Upload a Medtronic JSON recording file to the BRAVO platform.

        :param participant: Participant identifier for the uploaded data.
        :type participant: str
        :param file: File handle or tuple pair representing the uploaded file.
        :type file: tuple or file-like
        :param metadata: Additional metadata describing the device and recording context.
        :type metadata: dict
        :return: ``True`` when the upload succeeds.
        :rtype: bool
        :raises Exception: If the upload request fails.
        """
        form = {
            "File": file,
            "DataType": (None, "MedtronicJSON"),
            "ParticipantId": (None, participant),
            "Institute": (None, self.User["Institute"]),
            "Metadata": (None, json.dumps(metadata))
        }

        response = self.query("/api/uploadData", files=form, content_type=None)
        if response.status_code == 200:
            return True
        elif response.status_code == 301:
            return True
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")

    def UploadMATFile(self, participant, file, metadata=dict()):
        """Upload a MATLAB `.mat` file to the BRAVO platform.

        :param participant: Participant identifier for the uploaded data.
        :type participant: str
        :param file: File handle or tuple pair representing the uploaded file.
        :type file: tuple or file-like
        :param metadata: Additional upload metadata, including a default start time when omitted.
        :type metadata: dict
        :return: ``True`` when the upload succeeds.
        :rtype: bool
        :raises Exception: If the upload request fails.
        """
        if not "StartTime" in metadata:
            metadata["StartTime"] = datetime.datetime.now(datetime.timezone.utc).timestamp()

        form = {
            "File": file,
            "DataType": (None, "MATFile"),
            "ParticipantId": (None, participant),
            "Institute": (None, self.User["Institute"]),
            "Metadata": (None, json.dumps(metadata))
        }

        response = self.query("/api/uploadData", files=form, content_type=None)
        if response.status_code == 200:
            return True
        elif response.status_code == 301:
            return True
        else:
            if response.status_code == 400:
                raise Exception(f"Network Error: {response.json()}")
            else:
                raise Exception(f"Network Error: {response.status_code}")