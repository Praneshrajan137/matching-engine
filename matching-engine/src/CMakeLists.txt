# Source library for matching engine
add_library(matching_engine_lib
    order_book.cpp
)

target_include_directories(matching_engine_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Main executable (optional, for standalone testing)
# add_executable(matching_engine main.cpp)
# target_link_libraries(matching_engine matching_engine_lib)

