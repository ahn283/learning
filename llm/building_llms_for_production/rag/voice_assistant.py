import keyring
import os 
import openai
import streamlit as st 
from audio_recorder_streamlit import audio_recorder
from elevenlabs import ElevenLabs
from langchain.chains import RetrievalQA
from langchain.chat_models.openai import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import DeepLake
from streamlit_chat import message
import whisper

# Constants
TEMP_AUDIO_PATH = './temp/temp_audio.wav'
AUDIO_FORMAT = 'audio/wav'

# API Key
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
ELEVENLABS_API_KEY = keyring.get_password('elevenlabs', 'key_for_windows')
ACTIVELOOP_TOKEN = keyring.get_password('activeloop', 'key_for_windows')
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
os.environ['ELEVEN_API_KEY'] = ELEVENLABS_API_KEY
os.environ['ACTIVELOOP_TOKEN'] = ACTIVELOOP_TOKEN


def load_embeddings_and_database(active_loop_data_set_path):
    embeddings = OpenAIEmbeddings()
    db = DeepLake(
        dataset_path=active_loop_data_set_path,
        read_only=True,
        embedding_function=embeddings
    )
    return db


def transcribe_audio(audio_file_path):
   
    try:
        with open(audio_file_path, 'rb') as audio_file:
            # load the Whisper model
            model = whisper.load_model("base")
            # perform transcription
            result = model.transcribe(audio_file_path)
            return result['text']
    except Exception as e:
        print(f"Error calling Whisper API: {str(e)}")
        return None
    

# display the transcription of the audio on the app
def display_transcription(transcription):
    if transcription:
        st.write(f"Transciption: {transcription}")
        with open("/data/transcription.txt", 'w+') as f:
            f.write(transcription)
    else:
        st.write("Error transcribing audio.")

# get user input from Streamlit text input field
def get_user_input(transcription):
    return st.text_input("", value=transcription if transcription else "", key="input")


# record audio using audio_recorder and transcribe using transcibe_audio
def record_and_transribe_audio():
    audio_bytes = audio_recorder()
    transcription = None
    if audio_bytes:
        st.audio(audio_bytes, format=AUDIO_FORMAT)
        
        with open(TEMP_AUDIO_PATH, 'wb') as f:
            f.write(audio_bytes)
            
        if st.button("Transcribe"):
            transcription = transcribe_audio(TEMP_AUDIO_PATH)
            
        os.remove(TEMP_AUDIO_PATH)
        display_transcription(transcription)
        
    return transcription

# search the database for a response based on the user's query

def search_db(user_input, db):
    print(user_input)
    retriever = db.as_retriever()
    retriever.search_kwargs['distance_metric'] = 'cos'
    retriever.search_kwargs['fetch_k'] = 100
    retriever.search_kwargs['maximal_marginal_relevance'] = True
    retriever.search_kwargs['k'] = 4
    model = ChatOpenAI(model_name='gpt-3.5-turbo')
    qa = RetrievalQA.from_llm(model, retriever=retriever, return_source_documents=True)
    return qa({'query': user_input})


# display conversation history using streamlit messages
def display_conversation(history):
    """
    Display conversation history in Streamlit with ElevenLabs voice synthesis.

    Args:
        history (dict): A dictionary containing 'past' (user messages) and 'generated' (AI responses).
    """
    
    try:
        eleven = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        for i in range(len(history['generated'])):
            # Display user message
            message(history['past'][i], is_user=True, key=f"{i}_user")

            # Display AI response
            ai_text = history["generated"][i]
            message(ai_text, key=f"{i}_ai")

            # # Generate voice using ElevenLabs
            # voice = "Rachel"
            # audio = eleven.generate(text=ai_text, voice=voice)

            # # Display audio in Streamlit
            # st.audio(audio, format='audio/mp3')
            
            # generate voice using ElevenLabs
            voice = "Rachel"
            try:
                # get the audio as bianry data
                audio_generator = eleven.generate(text=ai_text, voice=voice)
                audio_data = b"".join(audio_generator)
                
                # play the audio in streamlit
                st.audio(audio_data, format='audio/mp3')
            except Exception as voice_error:
                st.warning(f"Could not generate audio for voice '{voice}")
            
    except Exception as e:
        st.error(f"Error displaying conversation: {str(e)}")

        
        
# main functio to run the app
def main():
    # dataset path
    my_activeloop_org_id = 'ahn283'
    my_activeloop_dataset_name = 'langchain_course_youtube_summarizer'
    dataset_path = f"hub://{my_activeloop_org_id}/{my_activeloop_dataset_name}"
    
    # initialize streamlit app with a title
    st.write("#JarvisBase")
    
    # load embeddings and the DeepLake database
    db = load_embeddings_and_database(dataset_path)
    
    # record and transribe audio
    transcription = record_and_transribe_audio()
    
    # get user input from text input or audio transciption
    user_input = get_user_input(transcription)
    
    # initialize session state for generated responses and past messages
    if "generated" not in st.session_state:
        st.session_state['generated'] = ['I am ready to help you']
    if "past" not in st.session_state:
        st.session_state['past'] = ['Hey there!']
        
    # search the database for a response based on user input and update the session state
    if user_input:
        output = search_db(user_input, db)
        print(output['source_douments'])
        st.session_state.past.append(user_input)
        response = str(output['result'])
        st.session_state.generated.append(response)
    
    # display conversation history using Streamlit messages
    if st.session_state['generated']:
        display_conversation(st.session_state)
        
# run the main function when the script is executed
if __name__ == "__main__":
    main()
        