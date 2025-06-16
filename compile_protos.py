import glob
from grpc_tools import protoc

protoc.main((
    '',
    '-I./mcp_gateway/protos',
    '-I./agents/validator/mcp_server ',
    '-I./agents/searcher/mcp_server ',
    '--python_out=./shared/protos/compiled',
    '--grpc_python_out=./shared/protos/compiled',
    *glob.glob('./mcp_gateway/protos/*.proto')
))

# import glob
# from grpc_tools import protoc

# # Compile main protos
# protoc.main((
#     '',
#     '-I./mcp_gateway/protos',
#     '-I./agents/validator/mcp_server',
#     '-I./agents/searcher/mcp_server',
#     '--python_out=./shared/protos/compiled',
#     '--grpc_python_out=./shared/protos/compiled',
#     *glob.glob('./mcp_gateway/protos/*.proto'),
#     *glob.glob('./agents/**/mcp_server/*.proto', recursive=True)
# ))

# # Create __init__.py files
# open('./shared/protos/compiled/__init__.py', 'a').close()