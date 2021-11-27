from .errors import WrongType
from .tools import MISSING, components_to_dict, setup_logger

import discord
from discord.http import Route

import json
import asyncio
from typing import List

logging = setup_logger(__name__)

class BetterRoute(Route):
    BASE = "https://discord.com/api/v9"

async def send_files(route, files, payload, http):
    """Sends files"""

    form = []
    form.append({'name': 'payload_json', 'value': json.dumps(payload, separators=(',', ':'), ensure_ascii=True)})

    if len(files) == 1:
        file = files[0]
        form.append({
            'name': 'file',
            'value': file.fp,
            'filename': file.filename,
            'content_type': 'application/octet-stream'
        })
    else:
        for index, file in enumerate(files):
            form.append({
                'name': 'file%s' % index,
                'value': file.fp,
                'filename': file.filename,
                'content_type': 'application/octet-stream'
            })

    return await http.request(route, form=form, files=files)

def get_message_payload(content=MISSING, tts=False, embed: discord.Embed=MISSING, embeds: List[discord.Embed]=MISSING, attachments: List[discord.Attachment]=MISSING, nonce: int=MISSING,
                allowed_mentions: discord.AllowedMentions=MISSING, reference: discord.MessageReference=MISSING, mention_author: bool=MISSING, components: list=MISSING, stickers: List[discord.Sticker]=MISSING, suppress: bool=MISSING, flags=MISSING):
    """Turns parameters from send functions into a payload for requests"""
    
    payload = {"tts": tts}

    if content is not MISSING:
        if content is None:
            payload["content"] = ""
        else:
            payload["content"] = str(content)

    if suppress not in [MISSING, None]:
        flags = discord.MessageFlags._from_value(flags or discord.MessageFlags.DEFAULT_VALUE)
        flags.suppress_embeds = suppress
        payload['flags'] = flags.value
    
    if nonce not in [MISSING, None]:
        payload["nonce"] = nonce
    
    if embed is not MISSING or embeds is not MISSING:
        if embeds is None and embed is None:
            embeds = []
        # if embed exsists and embeds doesn't exsist
        elif embed not in [MISSING, None] and embeds in [MISSING, None]:
            embeds = [embed]
        # if embed doesn't exsist and embeds does
        elif embed in [MISSING, None] and embeds not in [MISSING, None]:
            embeds = embed
        # check type things
        elif not all(isinstance(x, discord.Embed) for x in embeds):
            raise WrongType("embeds", embeds, 'list[discord.Embed]')
        payload["embeds"] = [em.to_dict() for em in embeds]

    if attachments is not MISSING:
        if attachments is None:
            payload["attachments"] = []
        else:
            if not all(isinstance(x, discord.Attachment) for x in attachments):
                raise WrongType("attachments", attachments, "List[discord.attachment]")
            payload["attachments"] = [x.to_dict() for x in attachments]

    if reference is not MISSING and reference is not None:
        if not isinstance(reference, (discord.MessageReference, discord.Message)):
            raise WrongType("reference", reference, ['discord.MessageReference', 'discord.Message'])
        if isinstance(reference, discord.MessageReference):
            payload["message_reference"] = reference.to_dict()
        elif isinstance(reference, discord.Message):
            payload["message_reference"] = discord.MessageReference.from_message(reference).to_dict()

    if allowed_mentions is not MISSING:
        if allowed_mentions is None:
            allowed_mentions = discord.AllowedMentions()
        else: 
            if not isinstance(allowed_mentions, discord.AllowedMentions):
                raise WrongType("allowed_mentions", allowed_mentions, "discord.AllowedMentions")
        payload["allowed_mentions"] = allowed_mentions.to_dict()
    if mention_author is not MISSING and mention_author is not None:
        allowed_mentions = payload["allowed_mentions"] if "allowed_mentions" in payload else discord.AllowedMentions().to_dict()
        allowed_mentions['replied_user'] = mention_author
        payload["allowed_mentions"] = allowed_mentions

    if components is not MISSING:
        if components is None:
            payload["components"] = []
        else:
            payload["components"] = components_to_dict(components)

    if stickers is not MISSING:
        if stickers is None:
            payload["stickers"] = []
        else:
            payload["stickers"] = [s.id for s in stickers]

    return payload

def handle_rate_limit(data):
    logging.error("You are being rate limited. Retrying after " + str(data["retry_after"]) + " seconds")
    return asyncio.sleep(data["retry_after"])