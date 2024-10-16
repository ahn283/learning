import streamlit as st 

st.title("First demo")
st.header("First header")
st.subheader("This is subheader")
st.text("This is text")
st.markdown("***markdown syntax***")
st.code('print("Hello, streamlit!")', language='python')

# input component
name = st.text_input("input name: ")
age = st.number_input("you age: ", min_value=0, max_value=120)

st.write("name: ", name)
st.write("age: ", age)

# button
if st.button("Confirm"):
    st.write("Confirmed")
else:
    st.write("Canceled")