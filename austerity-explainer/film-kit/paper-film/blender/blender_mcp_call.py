# What this does: talks to Blender Lab's official Blender MCP server (projects.blender.org/lab/
# blender_mcp) from the command line, so an agent without an MCP connection in its own tool list can
# still use the server's tools: inspect a scene (get_objects_summary, get_object_detail_summary),
# run Python in Blender (execute_blender_code), render a thumbnail (render_thumbnail_to_path), and
# search Blender's bundled Python API and user manual (search_api_docs, get_python_api_docs,
# search_manual_docs). It starts the server (`blender-mcp`, stdio), asks one thing, prints the answer
# (pictures are saved to files) and stops.
#
# Blender itself must already be running with the server's add-on, without a screen:
#   blender --background --online-mode --command blender_mcp --host 127.0.0.1 --port 9876
#
# Use (with the Python that has the `blender-mcp` package):
#   python blender_mcp_call.py tools                         list the tools and what each takes
#   python blender_mcp_call.py guide                         the server's own instructions to models
#   python blender_mcp_call.py TOOL '{"arg": "value"}'       call one tool; JSON arguments
#   python blender_mcp_call.py run-file SCRIPT.py            run a Python file in Blender
#                                                            (execute_blender_code with its text)
# Settings: BLENDER_MCP_SERVER (path to blender-mcp), BLENDER_PATH (the blender program, for the
# *_for_cli tools), BLENDER_MCP_HOST / BLENDER_MCP_PORT (where Blender listens), and
# BLENDER_MCP_PICTURES (folder for returned pictures, default the current folder).

import asyncio
import base64
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = os.environ.get('BLENDER_MCP_SERVER', 'blender-mcp')


async def main(arguments):
    parameters = StdioServerParameters(command=SERVER, args=[], env={**os.environ})
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            started = await session.initialize()
            what = arguments[0] if arguments else 'tools'
            if what == 'guide':
                print(started.instructions or '(the server gave no instructions)')
                prompts = await session.list_prompts()
                for prompt in prompts.prompts:
                    print(f'\nprompt: {prompt.name}: {prompt.description or ""}')
                return
            if what == 'tools':
                for tool in (await session.list_tools()).tools:
                    takes = ', '.join(tool.inputSchema.get('properties', {}).keys())
                    print(f'{tool.name}({takes})\n    {(tool.description or "").strip().splitlines()[0] if tool.description else ""}')
                return
            if what == 'run-file':
                code = open(arguments[1]).read()
                tool, payload = 'execute_blender_code', {'code': code}
            else:
                tool, payload = what, json.loads(arguments[1]) if len(arguments) > 1 else {}
            result = await session.call_tool(tool, payload)
            folder = os.environ.get('BLENDER_MCP_PICTURES', '.')
            for k, item in enumerate(result.content):
                if item.type == 'text':
                    print(item.text)
                elif item.type == 'image':
                    os.makedirs(folder, exist_ok=True)
                    path = os.path.join(folder, f'{tool}-{k}.png')
                    with open(path, 'wb') as out: out.write(base64.b64decode(item.data))
                    print(f'(picture saved: {path})')
            if result.isError: sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
