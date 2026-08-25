classdef BRAVOPlatformRequest
    % Request APIs to interface with BRAVO Platform (v3.0.0-alpha)
    %   Detailed explanation goes here
    
    properties
        APIKey
        ServerAddress
        Profile
    end
    
    methods
        function requester = BRAVOPlatformRequest(key, server)
            arguments
                key char
                server char = 'http://localhost:27286'
            end
            
            requester.APIKey = key;
            requester.ServerAddress = server;
            requester.Profile = GetUserInfo(requester);
        end
        
        %{  
        Example Usage:
            Profile = requester.GetUserInfo();
        %}
        function response = GetUserInfo(requester)
            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 5);
            response = webwrite([requester.ServerAddress '/api/queryProfile'], options);
        end
        
        %{  
        Example Usage:
            Config = requester.QueryAnalysisConfiguration();
        %}
        function response = QueryAnalysisConfiguration(requester, params)
            arguments
                requester
                params.config = false
            end

            data.Configurations = struct();
            if isa(params.config, 'struct')
                data.Configurations = params.config;
            end

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 5);
            response = webwrite([requester.ServerAddress '/api/queryProfile'], data, options);
        end
        
        function response = DeleteParticipant(requester, participant_uid)
            arguments
                requester
                participant_uid
            end

            data.ParticipantId = participant_uid;

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 500);
            response = webwrite([requester.ServerAddress '/api/deleteParticipantInformation'], data, options);
        end
        
        function response = AddNewParticipant(requester, participant_name)
            arguments
                requester
                participant_name
            end

            data.Name = participant_name;

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 5);
            response = webwrite([requester.ServerAddress '/api/createParticipantInformation'], data, options);
        end
        
        function response = AddNewDBSDevice(requester, participant_uid, device_type, device_serial)
            arguments
                requester
                participant_uid
                device_type
                device_serial
            end

            data.ParticipantId = participant_uid;
            data.DeviceType = "DBSDevice";
            data.ManufacturerDeviceType = device_type;
            data.SerialNumber = device_serial;

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 5);
            response = webwrite([requester.ServerAddress '/api/manageParticipantDevice'], data, options);
        end
        
        function response = QueryParticipants(requester)
            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 5);
            response = webwrite([requester.ServerAddress '/api/queryParticipants'], options);
        end
        
        function response = QueryParticipantInformation(requester, participant_uid)
            arguments
                requester
                participant_uid
            end

            data.ParticipantId = participant_uid;

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 5);
            response = webwrite([requester.ServerAddress '/api/queryParticipantInformation'], data, options);
        end
        
        % This include chronic events and patient controller events
        function response = QueryParticipantEvents(requester, participant_uid)
            arguments
                requester
                participant_uid
            end

            data.ParticipantId = participant_uid;

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 5);
            response = webwrite([requester.ServerAddress '/api/queryParticipantEvents'], data, options);
        end
        
        % This include chronic annotations and streaming annotations
        function response = QueryParticipantAnnotations(requester, participant_uid)
            arguments
                requester
                participant_uid
            end

            data.ParticipantId = participant_uid;

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 5);
            response = webwrite([requester.ServerAddress '/api/queryParticipantAnnotations'], data, options);
        end
        
        function response = QueryParticipantSurveyRecords(requester, participant_uid, form)
            arguments
                requester
                participant_uid
                form = false
            end

            data.ParticipantId = participant_uid;
            data.RequestType = 'RequestAll';
            
            if isstruct(form)
                data.RequestType = 'RequestRecords';
                data.FormId = form.Id;
            end

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 5);
            response = webwrite([requester.ServerAddress '/api/queryParticipantSurveyRecords'], data, options);

            if isstruct(form)
                numRecords = length(response);
                SurveyResponses = struct('Date', cell(1, numRecords), 'Response', []);
                for i = 1:numRecords
                    SurveyResponse = struct();
                    SurveyResponse.Date = response(i).Date;
                    responsesList = {}; 
                    for page = 1:length(form.Record)
                        for question = 1:length(form.Record(page).questions)
                            res = struct();
                            res.Question = form.Record(page).questions{question}.text;
                            res.Type = form.Record(page).questions{question}.type;
                            res.Response = response(i).Result{page}{question};
                            
                            % Append to cell array
                            responsesList{end+1} = res;
                        end
                    end
                    SurveyResponse.Response = [responsesList{:}];
                    SurveyResponses(i) = SurveyResponse;
                end
                response = SurveyResponses;
            end
        end
        
        function response = QueryTimeseriesAnalysis(requester, participant_uid, params)
            arguments
                requester
                participant_uid
                params.recording_id = false
                params.config = false
                params.refresh = false
            end

            import matlab.net.http.*
            import matlab.net.http.field.*
            import matlab.net.http.io.*
            
            data.ParticipantId = participant_uid;
            data.RequestType = 'Overview';

            if params.refresh
                data.RequestType = "DeleteCache";
                data.AnalysisId = params.recording_id;
                data.TherapyId = null;
                options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
                webwrite([requester.ServerAddress '/api/queryTimeseriesAnalysis'], data, options);

                params.refresh = false;
                params = namedargs2cell(params);
                response = QueryTimeseriesAnalysis(requester, participant_uid, params{:});
                return;
            end

            if isa(params.recording_id, 'char') || isa(params.recording_id, 'string')
                data.RequestType = 'RequestData';
                data.RecordingId = params.recording_id;
                data.ActiveChannels = 'RequestAllChannel';
            end

            if isa(params.config, 'struct')
                data.ProcessingConfiguration = params.config;
            end
            
            if strcmp(data.RequestType, 'Overview')
                options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'ContentType', 'json', 'Timeout', 60);
                response = webwrite([requester.ServerAddress '/api/v2/queryTimeseriesAnalysis'], data, options);
                return;
            elseif strcmp(data.RequestType, 'RequestData')
                endpoint = [requester.ServerAddress, '/api/v2/queryTimeseriesAnalysis'];
                headers = [ ...
                    HeaderField('X-Secure-API-Key', requester.APIKey), ...
                    HeaderField('Accept', 'application/octet-stream') ...
                ];
                body = MessageBody(data);
                request = RequestMessage(RequestMethod.POST, headers, body);
                options = HTTPOptions('ConnectTimeout', 60);
                responseMessage = request.send(endpoint, options);
                
                responseHeaders = responseMessage.Header;
                metadata = responseHeaders.getFields('X-Timeseries-Metadata');
                response = jsondecode(metadata.Value);
                response.Data = zstd_decompress(responseMessage.Body.Data);
                response.Data = reshape(typecast(response.Data, 'double'), fliplr(response.DataShape'))';
                return
            end
        end
        
        function response = QueryChronicNeuralActivity(requester, participant_uid, params)
            arguments
                requester
                participant_uid
                params.refresh = false
            end

            data.ParticipantId = participant_uid;
            data.RequestType = 'RequestAll';

            if params.refresh
                data.RequestType = "DeleteCache";
                options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
                webwrite([requester.ServerAddress '/api/queryChronicNeuralActivity'], data, options);

                params.refresh = false;
                params = namedargs2cell(params);
                response = QueryChronicNeuralActivity(requester, participant_uid, params{:});
                return;
            end

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
            response = webwrite([requester.ServerAddress '/api/queryChronicNeuralActivity'], data, options);
        end
        
        function response = QueryChronicTimeline(requester, participant_uid, params)
            arguments
                requester
                participant_uid
                params.refresh = false
            end

            data.ParticipantId = participant_uid;
            data.RequestType = 'RequestAll';

            if params.refresh
                data.RequestType = "DeleteCache";
                options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
                webwrite([requester.ServerAddress '/api/queryChronicTimeline'], data, options);

                params.refresh = false;
                params = namedargs2cell(params);
                response = QueryChronicTimeline(requester, participant_uid, params{:});
                return;
            end

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
            response = webwrite([requester.ServerAddress '/api/queryChronicTimeline'], data, options);
        end
        
        function response = QueryNeuralActivitySnapshot(requester, participant_uid, params)
            arguments
                requester
                participant_uid
                params.refresh = false
                params.config = false
            end

            data.ParticipantId = participant_uid;
            data.RequestType = 'RequestAll';
            
            if class(params.config) == "struct"
                data.ProcessingConfiguration = params.config;
            end

            if params.refresh
                data.RequestType = "DeleteCache";
                options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
                webwrite([requester.ServerAddress '/api/queryNeuralActivitySnapshot'], data, options);

                params.refresh = false;
                params = namedargs2cell(params);
                response = QueryNeuralActivitySnapshot(requester, participant_uid, params{:});
                return;
            end

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
            response = webwrite([requester.ServerAddress '/api/queryNeuralActivitySnapshot'], data, options);
        end
        
        function response = QueryTherapyHistory(requester, participant_uid)
            arguments
                requester
                participant_uid
            end

            data.ParticipantId = participant_uid;
            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
            response = webwrite([requester.ServerAddress '/api/queryTherapyHistory'], data, options);
        end

        function response = QueryMedicationCycleAnalysis(requester, participant_uid, params)
            arguments
                requester
                participant_uid
                params.recording_ids = false
            end

            data.ParticipantId = participant_uid;
            data.RequestType = 'RequestAll';

            if isa(params.recording_ids, 'cell')
                data.RequestType = 'RequestAnalysis';
                data.RecordingIds = params.recording_ids;
            end

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
            response = webwrite([requester.ServerAddress '/api/queryMedicationCycleAnalysis'], data, options);
        end

        function response = RequestAIPrediction(requester, analysis_name, input)
            arguments
                requester
                analysis_name,
                input
            end
            
            data.RequestType = 'RequestAnalysis';
            data.AnalysisName = analysis_name;
            data.Data = input;

            options = weboptions('HeaderFields', {'X-Secure-API-Key' requester.APIKey;}, 'Timeout', 60);
            response = webwrite([requester.ServerAddress '/api/requestAIPrediction'], data, options);
        end
    end
end

