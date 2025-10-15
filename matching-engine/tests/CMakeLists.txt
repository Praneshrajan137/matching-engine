# Fetch Google Test framework
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)

# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

enable_testing()

# Test executable
add_executable(
  order_book_tests
  test_order_book.cpp
)

target_include_directories(order_book_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/src
)

target_link_libraries(order_book_tests
    matching_engine_lib
    gtest_main
    gmock_main
)

# Discover tests
include(GoogleTest)
gtest_discover_tests(order_book_tests)

