% Get API Key from Profile page.
requester = BRAVOPlatformRequest('', 'https://bravo.rc.ufl.edu');

% Get List of patients
Participants = requester.QueryParticipants();
Participant = Participants(3);

% Get list of all timeseries recordings
Recordings = requester.QueryTimeseriesAnalysis(Participant.Id);

% Get raw data and how alignment will be handled
Data = requester.QueryTimeseriesAnalysis(Participant.Id, 'recording_id', Recordings{2}.Id);
Time = (0:Data.DataShape(2)-1) / Data.SamplingRate + Data.StartTime + Recordings{2}.Alignment;
Time = datetime(Time, 'ConvertFrom', 'posixtime');

% Quick check
fig = largeFigure(1, [800,600]);
subplot(1,1,1);
plot(dt, Data.Data(1,:));
xtickformat('yyyy-MM-dd HH:mm:ss');
xlabel('Time');
ylabel('Amplitude');

% PSDs from Surveys
Surveys = requester.QueryNeuralActivitySnapshot(Participant.Id);

% Survey Responses
Forms = requester.QueryParticipantSurveyRecords(Participant.Id);
DesireForm = Forms.Forms(1);
Records = requester.QueryParticipantSurveyRecords(Participant.Id, DesireForm);

