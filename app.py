# coding: utf-8
from typing import Optional
import ssl
import re

import certifi
from fastapi import FastAPI, status, HTTPException
import aiohttp
from bs4 import BeautifulSoup


app = FastAPI()


@app.get("/")
async def check_nuxt_build_mode(url: str, user_agent: Optional[str] = None):

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    headers = {"User-Agent": user_agent or ""}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=ssl_context, headers=headers) as resp:
                if 200 > resp.status >= 300:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"bad status code, code: {resp.status}",
                    )

                text = await resp.text()
                soup = BeautifulSoup(text, "html5lib")
                scripts = [
                    x.get("src") for x in soup.find_all("script") if x.get("src")
                ]
                if not scripts:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="no script balise found",
                    )
                for script_src in scripts:
                    m = re.match("/_nuxt/\w+.modern.js", script_src)
                    if m is not None:
                        return {"result": True, "debug": {"scripts": scripts}}
                return {"result": False, "debug": {"scripts": scripts}}

    except aiohttp.client_exceptions.ClientConnectorError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except aiohttp.client_exceptions.InvalidURL:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invalid url")

    except Exception as e:
        print(type(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
