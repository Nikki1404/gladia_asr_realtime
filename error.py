Saved metrics to: C:\Users\re_nikitav\Documents\azure_benchmarking\audio\a.metrics.json
(client_env) PS C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script> ^C
(client_env) PS C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script> python .\gladia_client.py --mode file --file C:/Users/re_nikitav/Documents/azure_benchmarking/audio/a.wav --language en --chunk-ms 30
{'type': 'ready', 'session_id': '059315e3-e80a-40ac-b177-d457f68ee6ec', 'language': 'en', 'sample_rate': 16000, 'message': 'WebSocket connected. Send config first, then PCM16 audio bytes.'}
{'type': 'loading', 'session_id': '059315e3-e80a-40ac-b177-d457f68ee6ec', 'language': 'en', 'message': 'Loading ASR router, Silero VAD, and SpeechBrain LID'}
{'type': 'config_ack', 'session_id': '059315e3-e80a-40ac-b177-d457f68ee6ec', 'language': 'en', 'sample_rate': 16000}
{'type': 'audio_received', 'session_id': '059315e3-e80a-40ac-b177-d457f68ee6ec', 'language': 'en', 'text': '', 'asr_confidence': None, 'ttfb_ms': 0.29, 'ttft_ms': None, 'elapsed_ms': 0.29, 'utterance_ttfb_ms': 0.0, 'utterance_ttft_ms': None}
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EX
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITION
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELI
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUP
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUPPORT
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUPPORT THIS
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUPPORT THIS IS SA
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUPPORT THIS IS SARAH
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUPPORT THIS IS SARAH HOW
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUPPORT THIS IS SARAH HOW CAN I HE
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUPPORT THIS IS SARAH HOW CAN I HELP YOU
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUPPORT THIS IS SARAH HOW CAN I HELP YOU TO DAY

UTTERANCE_FINAL [en] ttfb=0.29ms ttft=2098.29ms lid_conf=1.0 lid_label=en: English : THANK YOU FOR CALLING EVEREST EXPEDITIONS DELIVERY SUPPORT THIS IS SARAH HOW CAN I HELP YOU TO DAY
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDER
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTA
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR TRACKING
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR TRACKING NUMBER
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR TRACKING NUMBER WHERE THE
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR TRACKING NUMBER WHERE THE NAME ON
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR TRACKING NUMBER WHERE THE NAME ON THE ORD
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR TRACKING NUMBER WHERE THE NAME ON THE ORDERS I
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR TRACKING NUMBER WHERE THE NAME ON THE ORDERS I CAN LOOK
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR TRACKING NUMBER WHERE THE NAME ON THE ORDERS I CAN LOOK INTO IT
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : I UNDERSTAND CAN I GET YOUR TRACKING NUMBER WHERE THE NAME ON THE ORDERS I CAN LOOK INTO IT FOR

UTTERANCE_FINAL [en] ttfb=0.29ms ttft=2098.29ms lid_conf=0.9999 lid_label=en: English : I UNDERSTAND CAN I GET YOUR TRACKING NUMBER WHERE THE NAME ON THE ORDERS I CAN LOOK INTO IT FOR YOU
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFOR
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I SEE
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I SEE YOUR PA
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I SEE YOUR PACKAGE
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I SEE YOUR PACKAGE AS MAR
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I SEE YOUR PACKAGE AS MARKED AS
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I SEE YOUR PACKAGE AS MARKED AS OUT FOR
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I SEE YOUR PACKAGE AS MARKED AS OUT FOR DELI
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I SEE YOUR PACKAGE AS MARKED AS OUT FOR DELIVERY
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : THANKS LET ME PULL THAT INFORMATION UP O K I SEE YOUR PACKAGE AS MARKED AS OUT FOR DELIVERY TO

UTTERANCE_FINAL [en] ttfb=0.29ms ttft=2098.29ms lid_conf=1.0 lid_label=en: English : THANKS LET ME PULL THAT INFORMATION UP O K I SEE YOUR PACKAGE AS MARKED AS OUT FOR DELIVERY TO DAY
PARTIAL [en] ttfb=0.29ms ttft=2098.29ms conf=None : SOME
