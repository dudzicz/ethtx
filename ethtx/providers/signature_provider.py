#  Copyright 2021 DAI Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Iterator, TypedDict

import requests


class SignatureReturnType(TypedDict):
    name: str
    args: List[str]


class SignatureProvider(ABC):
    @abstractmethod
    def list_function_signatures(self, filters: Dict):
        ...

    @abstractmethod
    def list_event_signatures(self, filters: Dict):
        ...

    @abstractmethod
    def get_function(self, signature: str):
        ...

    @abstractmethod
    def get_event(self, signature: str):
        ...


class FourByteProvider(SignatureProvider):
    API_URL: str = "https://www.4byte.directory/api/v1"
    FUNCTION_ENDPOINT: str = "signatures"
    EVENT_ENDPOINT: str = "event-signatures"

    def list_function_signatures(self, filters: Dict = None) -> List[Dict]:
        return self._get_all(endpoint=self.FUNCTION_ENDPOINT, filters=filters)

    def list_event_signatures(self, filters: Dict = None) -> List[Dict]:
        return self._get_all(endpoint=self.EVENT_ENDPOINT, filters=filters)

    def get_function(self, signature: str) -> Iterator[SignatureReturnType]:
        if signature == "0x":
            raise ValueError(f"Signature can not be: {signature}")

        data = self._get_all(
            endpoint=self.FUNCTION_ENDPOINT, filters={"hex_signature": signature}
        )

        for function in reversed(data):
            yield self._parse_text_signature_response(function)

    def get_event(self, signature: str) -> Iterator[SignatureReturnType]:
        if signature == "0x":
            raise ValueError(f"Signature can not be: {signature}")

        data = self._get_all(
            endpoint=self.EVENT_ENDPOINT, filters={"hex_signature": signature}
        )

        for event in reversed(data):
            yield self._parse_text_signature_response(event)

    def url(self, endpoint: str) -> str:
        return f"{self.API_URL}/{endpoint}/"

    def _get_all(self, endpoint: str, filters: Dict = None) -> List[Dict]:
        page = 1
        results = []

        while True:
            res = self._get(endpoint, page, filters)
            next_url = res.get("next")
            results.extend(res.get("results", []))

            if not next_url:
                break
            page += 1

        return results

    def _get(
        self, endpoint: str, page: int = 0, filters: Dict = None
    ) -> Dict[str, Any]:
        if filters is None:
            filters = {}

        if page:
            filters["page"] = page

        return requests.get(self.url(endpoint), params=filters).json()

    @staticmethod
    def _parse_text_signature_response(data: Dict) -> SignatureReturnType:
        text_sig = data.get("text_signature", "")
        name = text_sig.split("(")[0] if text_sig else ""

        types = (
            text_sig[text_sig.find("(") + 1 : text_sig.rfind(")")] if text_sig else ""
        )
        if "(" in types:
            types = types[types.find("(") + 1 : types.rfind(")")]

        return {"name": name, "args": types.split(",")}


FourByteProvider = FourByteProvider()