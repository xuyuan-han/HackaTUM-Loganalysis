#!/usr/bin/env python3
from typing import List, Tuple

from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from log_callback_handler import NiceGuiLogElementCallbackHandler
from Lc_read import load_log,qa_langchain

from nicegui import context, ui,events
import os

OPENAI_API_KEY = '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'  # TODO: set your OpenAI API key here


@ui.page('/')
def main():
    llm = ConversationChain(llm=ChatOpenAI(model_name='gpt-3.5-turbo', openai_api_key=OPENAI_API_KEY))

    messages: List[Tuple[str, str]] = []
    thinking: bool = False
    
    

    def handle_upload(e: events.UploadEventArguments):
        text = e.content.read().decode('utf-8')
        
        if os.path.exists('data.txt'):
            os.remove('data.txt')
        
        with open('data.txt', 'w') as file:
            file.write(text)
    ui.upload(on_upload=handle_upload).props('accept=.out').classes('max-w-full')
    
    
    @ui.refreshable
    def loading() -> None:
        ui.label('loading...')   
        
    

    def load_log_callback():
        loading.refresh()
        global vectorstore
        vectorstore = load_log('data.txt')
        print('finish loading log')
        messages.clear()  # Clear the existing chat messages
        messages.append(('Bot', 'Log file loaded successfully.'))  # Add a system message
        chat_messages.refresh()  # Refresh the chat messages UI

    ui.button('Click me!', on_click=load_log_callback)
   
    
    @ui.refreshable
    def chat_messages() -> None:
        for name, text in messages:
            ui.chat_message(text=text, name=name, sent=name == 'You')
        if thinking:
            ui.spinner(size='3rem').classes('self-center')
        if context.get_client().has_socket_connection:
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')

    async def send() -> None:
        nonlocal thinking
        message = text.value
        messages.append(('You', text.value))
        thinking = False
        text.value = ''
        chat_messages.refresh()

        # response = qa_langchain(message)
        response = qa_langchain(message,vectorstore)
        messages.append(('Bot', response))
        thinking = False
        chat_messages.refresh()

    # anchor_style = r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}'
    # ui.add_head_html(f'<style>{anchor_style}</style>')

    # the queries below are used to expand the contend down to the footer (content can then use flex-grow to expand)
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')

    with ui.tabs().classes('w-full') as tabs:
        chat_tab = ui.tab('Chat')
        logs_tab = ui.tab('Logs')
    with ui.tab_panels(tabs, value=chat_tab).classes('w-full max-w-2xl mx-auto flex-grow items-stretch'):
        with ui.tab_panel(chat_tab).classes('items-stretch'):
            chat_messages()
        with ui.tab_panel(logs_tab):
            log = ui.log().classes('w-full h-full')

    with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
        with ui.row().classes('w-full no-wrap items-center'):
            placeholder = 'message' 
            text = ui.input(placeholder=placeholder).props('rounded outlined input-class=mx-3') \
                .classes('w-full self-center').on('keydown.enter', send)
        ui.markdown('simple chat app built with [NiceGUI](https://nicegui.io)') \
            .classes('text-xs self-end mr-8 m-[-1em] text-primary')


ui.run(title='log Reader')

