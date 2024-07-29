##### 기본 정보 입력 #####
import streamlit as st
# audiorecorder 패키지 추가
from audiorecorder import audiorecorder
# OpenAI 패키지 추가
import openai
# 파일 삭제를 위한 패키지 추가
import os
# 시간 정보를 위한 패키지 추가
from datetime import datetime
# TTS 패키기 추가
from gtts import gTTS
# 음원 파일 재생을 위한 패키지 추가
import base64
# 오디오 파일의 처리를 위한 패키지 추가
from pydub import AudioSegment
import ffmpeg

#### 기능 구현 함수 ####
def STT(audio, apikey):
    # 파일 저장
    filename = 'input.mp3'
    audio.export(filename, format="mp3")  # Whisper 모델은 '파일 형태'의 음원 입력받음
    
    # 오디오 파일 열기
    with open(filename, "rb") as audio_file:
        # Whisper 모델을 활용해 텍스트 얻기
        client = openai.OpenAI(api_key=apikey)
        response = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    
    # 파일 삭제
    os.remove(filename)
    
    # Transcription 객체에서 텍스트 추출
    # response는 Transcription 객체로 가정
    try:
        transcription_text = response.text  # 또는 다른 속성/메서드를 사용해야 할 수도 있음
    except AttributeError:
        transcription_text = "Transcription text not found."
    
    return transcription_text


def ask_gpt(prompt, model,apikey):
    client = openai.OpenAI(api_key=apikey)
     
    # ChatCompletion API 호출
    response = client.chat.completions.create(model=model, messages=prompt)
    
     # 'choices' 리스트에서 첫 번째 항목의 'message' 속성에서 'content'를 추출
    try:
         # response.choices[0].message는 객체이며 서브스크립트 방식으로 접근할 수 없음
        gptResponse = response.choices[0].message.content
    except (IndexError, KeyError) as e:
        gptResponse = f"Error retrieving response: {str(e)}"
    
    return gptResponse

def TTS(response):
    # gTTS 를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response,lang="ko")
    tts.save(filename)

    # 음원 파일 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3"> 
            </audio>
            """  #gTTS는 mp3 포맷으로만 음성 파일 저장 가능.
        st.markdown(md,unsafe_allow_html=True,)
    # 파일 삭제
    os.remove(filename)

##### 기본 설명 영역 #####
  #### 메인 함수 ####
def main():
    # 기본 설정
    st.set_page_config(
        page_title="음성 비서 프로그램",
        layout="wide"
    )

    # session_state 없을 시 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""  # 기본값을 빈 문자열로 설정

    # 제목
    st.header("음성 비서 프로그램")
    st.markdown("---")

    # 기본 설명
    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
        """     
        - 음성비서 프로그램의 UI는 스트림릿을 활용했습니다.
        - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용했습니다. 
        - 답변은 OpenAI의 GPT 모델을 활용했습니다. 
        - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용했습니다.
        """
        )
        st.markdown("")

    # 사이드바 생성
    with st.sidebar:
        # Open AI API 키 입력받기
        st.session_state["OPENAI_API"] = st.text_input(label="OPENAI API 키", placeholder="Enter Your API Key", value=st.session_state["OPENAI_API"], type="password")

        st.markdown("---")

        # GPT 모델 선택을 위한 라디오 버튼 생성
        model = st.radio(label="GPT 모델", options=["gpt-4", "gpt-3.5-turbo"])

        st.markdown("---")

        # 리셋 버튼 생성
        if st.button(label="초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]
            st.session_state["check_reset"] = True
            
    # 기능 구현 영역
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("질문하기")
        audio = audiorecorder("클릭하여 녹음하기", "녹음중...")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):
            st.audio(audio.export().read())
            question = STT(audio, st.session_state["OPENAI_API"])

            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("user", now, question)]
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "user", "content": question}]

    with col2:
        st.subheader("질문/답변")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):
            response = ask_gpt(st.session_state["messages"], model, st.session_state["OPENAI_API"])

            st.session_state["messages"] = st.session_state["messages"] + [{"role": "system", "content": response}]

            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]

            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")

            TTS(response)
        else:
            st.session_state["check_reset"] = False

if __name__ == "__main__":
    main()