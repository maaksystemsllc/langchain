"""Fake ChatModel for testing purposes."""
import asyncio
import time
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel, SimpleChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage, BaseMessageChunk
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult


class FakeMessagesListChatModel(BaseChatModel):
    """Fake ChatModel for testing purposes."""

    responses: Union[
        List[Union[BaseMessage, BaseMessageChunk, str]],
        List[List[Union[BaseMessage, BaseMessageChunk, str]]],
    ]
    sleep: Optional[float] = None
    i: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake-messages-list-chat-model"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"responses": self.responses}

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        response = self._call(messages, stop=stop, run_manager=run_manager, **kwargs)
        responses = response if isinstance(response, list) else [response]
        generations = [ChatGeneration(message=res) for res in responses]
        return ChatResult(generations=generations)

    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Union[BaseMessage, List[BaseMessage]]:
        """Rotate through responses."""
        response = self.responses[self.i]
        if self.i < len(self.responses) - 1:
            self.i += 1
        else:
            self.i = 0
        if isinstance(response, str):
            response = BaseMessage(content=response)
        elif isinstance(response, BaseMessage):
            pass
        elif isinstance(response, list):
            for i, item in enumerate(response):
                if isinstance(item, str):
                    response[i] = BaseMessage(content=item)
                elif not isinstance(item, BaseMessage):
                    raise TypeError(f"Unexpected type in response list: {type(item)}")
        else:
            raise TypeError(f"Unexpected type for response: {type(response)}")
        return response

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Union[List[str], None] = None,
        run_manager: Union[CallbackManagerForLLMRun, None] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Rotate through responses."""
        response = self.responses[self.i]
        if self.i < len(self.responses) - 1:
            self.i += 1
        else:
            self.i = 0
        for c in response:
            if self.sleep is not None:
                time.sleep(self.sleep)
            if isinstance(c, AIMessageChunk):
                chunk = c
            elif isinstance(c, str):
                chunk = AIMessageChunk(content=c)
            else:
                raise TypeError(f"Unexpected type for response chunk: {type(c)}")
            yield ChatGenerationChunk(message=chunk)

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Union[List[str], None] = None,
        run_manager: Union[AsyncCallbackManagerForLLMRun, None] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """Rotate through responses."""
        response = self.responses[self.i]
        if self.i < len(self.responses) - 1:
            self.i += 1
        else:
            self.i = 0
        for c in response:
            if self.sleep is not None:
                await asyncio.sleep(self.sleep)
            if isinstance(c, AIMessageChunk):
                chunk = c
            elif isinstance(c, str):
                chunk = AIMessageChunk(content=c)
            else:
                raise TypeError(f"Unexpected type for response chunk: {type(c)}")
            yield ChatGenerationChunk(message=chunk)


class FakeListChatModel(SimpleChatModel):
    """Fake ChatModel for testing purposes."""

    responses: List
    sleep: Optional[float] = None
    i: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake-list-chat-model"

    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """First try to lookup in queries, else return 'foo' or 'bar'."""
        response = self.responses[self.i]
        if self.i < len(self.responses) - 1:
            self.i += 1
        else:
            self.i = 0
        return response

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Union[List[str], None] = None,
        run_manager: Union[CallbackManagerForLLMRun, None] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        response = self.responses[self.i]
        if self.i < len(self.responses) - 1:
            self.i += 1
        else:
            self.i = 0
        for c in response:
            if self.sleep is not None:
                time.sleep(self.sleep)
            yield ChatGenerationChunk(message=AIMessageChunk(content=c))

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Union[List[str], None] = None,
        run_manager: Union[AsyncCallbackManagerForLLMRun, None] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        response = self.responses[self.i]
        if self.i < len(self.responses) - 1:
            self.i += 1
        else:
            self.i = 0
        for c in response:
            if self.sleep is not None:
                await asyncio.sleep(self.sleep)
            yield ChatGenerationChunk(message=AIMessageChunk(content=c))

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"responses": self.responses}
