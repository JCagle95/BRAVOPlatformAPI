# BRAVOClient

Python and MATLAB clients for the Brain Recording Analysis and Visualization Online (BRAVO) platform.

BRAVOClient provides a convenient interface for interacting with a BRAVO server from Python and MATLAB. It exposes a `BRAVOPlatformRequest` client for querying participant and study information, retrieving neural time-series and analysis data, uploading recordings, managing surveys, and accessing platform configuration defaults. The project also includes a MATLAB API client implementation for equivalent access to the same BRAVO platform services.

## Overview

The BRAVO platform is designed for the storage, review, and analysis of brain-recording data, participant metadata, therapeutic histories, and signal-processing outputs. This SDK wraps the BRAVO REST API so that researchers and developers can programmatically access the platform without building raw HTTP requests by hand. It is available in both Python and MATLAB client implementations for cross-language research workflows.

The package includes:

- user and participant profile queries
- study creation and participant assignment
- time-series and neural activity analysis access
- therapeutic effect and chronic data queries
- survey form management and response submission
- data uploads for MAT and Medtronic JSON files
- built-in default processing configuration presets

## Installation

### Python

Install from PyPI:

```bash
pip install BRAVOClient
```

Or install directly from this repository:

```bash
git clone https://github.com/JCagle95/BRAVOPlatformAPI
cd BRAVOPlatformAPI
pip install .
```

### MATLAB

To use the MATLAB client, add the `matlab` directory to your MATLAB path:

```matlab
addpath('path/to/BRAVOPlatformAPI/matlab');
```

Then instantiate the client:

```matlab
requester = BRAVOPlatformRequest('YOUR_API_KEY', 'http://localhost:27286');
profile = requester.GetUserInfo();
```

## Requirements

### Python

- Python 3.8+
- `requests`
- `numpy`
- `zstandard`

### MATLAB

- MATLAB R2020b or later
- Network access to the BRAVO server
- Valid BRAVO API key

## Quick Start

```python
from BRAVOClient import BRAVOPlatformRequest, DefaultConfigurations

client = BRAVOPlatformRequest(
    api_key="YOUR_API_KEY",
    server="http://localhost:27286",
)

# Fetch the authenticated user profile
profile = client.GetUserInfo()
print(profile)

# Query participants
Participants = client.QueryParticipants()
Participant = [participant for participant in Participants if participant["Name"] == "Demo Patient"][0]

```

The constructor automatically validates the API key by requesting profile information from the BRAVO server.

## Querying Time-Series Analysis

The client includes default processing configuration presets for common analysis workflows:

```python
from BRAVOClient import BRAVOPlatformRequest, DefaultConfigurations

client = BRAVOPlatformRequest(api_key="YOUR_API_KEY")

Recordings = client.QueryTimeSeriesAnalysis(Participant["Id"])
Recording = [recording for recording in Recordings if recording["Id"] == "RECORDING_UID"][0]
Data = client.QueryTimeSeriesAnalysis(Participant["Id"], Recording["Id"])

```

This is useful for requesting processed recordings, metadata, and analysis outputs from the platform.

## Common API Features

The client exposes methods for the most common BRAVO operations, including:

- `GetUserInfo()`
- `QueryParticipants()`
- `QueryParticipantInformation(participant_uid)`
- `UpdateParticipantInformation(participant_uid, info)`
- `ListAllStudies()`
- `CreateNewStudy(study_name)`
- `AddParticipantToStudy(study_id, participant_uid)`
- `QueryTherapyHistory(participant_uid)`
- `QueryTimeSeriesAnalysis(participant_uid, recording_uid=None, config=None, refresh=False)`
- `QueryNeuralActivitySnapshot(participant_uid, config=None)`
- `QuerySurveyForms(form_link=None, version=None)`
- `CreateSurveyForm(institute, form_name)`
- `SubmitSurveyResponse(form_uid, version, responder_code, result, date=None)`
- `UploadMATFile(participant, file, metadata={})`
- `UploadMedtronicJSON(participant, file, metadata={})`

## License

This project is distributed under the MIT License.

## Project URL

- Homepage: https://github.com/Fixel-Institute/BRAVO
- Issue Tracker: https://github.com/Fixel-Institute/BRAVO/issues

## Support

If you are using this client against a BRAVO deployment, make sure the server is reachable from your environment and that your API key is valid for the target instance.
