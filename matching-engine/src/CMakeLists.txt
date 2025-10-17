# Source library for matching engine
add_library(matching_engine_lib
    order_book.cpp
    matching_engine.cpp
)

target_include_directories(matching_engine_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Engine Runner - PRODUCTION executable with FULL Redis integration
# Uses custom Redis client (redis_client.hpp) built on Windows Sockets
add_executable(engine_runner engine_runner.cpp)
target_link_libraries(engine_runner matching_engine_lib)

# Link Windows Sockets library for Redis client
if(WIN32)
    target_link_libraries(engine_runner ws2_32)
endif()

