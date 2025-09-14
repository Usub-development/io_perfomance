cmake_minimum_required(VERSION 3.20)
project(bench_uvent C CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_C_STANDARD 11)

option(WITH_UVENT "Build uvent echo" ON)
option(WITH_ASIO "Build Boost.Asio echo" ON)
option(WITH_LIBUV "Build libuv echo" ON)
option(ENABLE_LTO "Enable link-time optimization" OFF)

if (CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    add_compile_options(-O3 -DNDEBUG -march=native -fno-omit-frame-pointer -Wall -Wextra -Wpedantic -Wno-unused-parameter)
    add_compile_options(-fexceptions -fno-rtti)
elseif (MSVC)
    add_compile_options(/O2 /DNDEBUG /permissive- /W4)
endif()

if (UNIX)
    add_link_options(-pthread)
endif()

include(FetchContent)

FetchContent_Declare(uvent
        GIT_REPOSITORY https://github.com/Usub-development/uvent.git
        GIT_TAG main
        GIT_SHALLOW TRUE
        GIT_PROGRESS TRUE
)
FetchContent_MakeAvailable(uvent)

if (TARGET usub::uvent)
elseif (TARGET uvent)
    add_library(usub::uvent ALIAS uvent)
elseif (TARGET Uvent)
    add_library(usub::uvent ALIAS Uvent)
elseif (TARGET usub_uvent)
    add_library(usub::uvent ALIAS usub_uvent)
else()
    add_library(uvent INTERFACE)
    target_include_directories(uvent INTERFACE ${uvent_SOURCE_DIR}/include)
    add_library(usub::uvent ALIAS uvent)
endif()

include_directories(${CMAKE_SOURCE_DIR}/include)

if (WITH_UVENT)
    add_executable(echo_uvent src/echo_tcp/uvent_server.cpp)
    target_link_libraries(echo_uvent PRIVATE usub::uvent pthread)
    if (ENABLE_LTO)
        include(CheckIPOSupported)
        check_ipo_supported(RESULT _ipo)
        if (_ipo)
            set_property(TARGET echo_uvent PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
        endif()
    endif()
endif()

if (WITH_ASIO)
    find_package(Boost 1.70 REQUIRED COMPONENTS system)
    add_executable(echo_asio src/echo_tcp/asio_server.cpp)
    target_compile_options(echo_asio PRIVATE -fexceptions -frtti)
    target_link_libraries(echo_asio PRIVATE Boost::system pthread)
    if (ENABLE_LTO)
        include(CheckIPOSupported)
        check_ipo_supported(RESULT _ipo)
        if (_ipo)
            set_property(TARGET echo_asio PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
        endif()
    endif()
endif()

FetchContent_Declare(libuv
        GIT_REPOSITORY https://github.com/libuv/libuv.git
        GIT_TAG v1.49.2
        GIT_SHALLOW TRUE
        GIT_PROGRESS TRUE
)
FetchContent_MakeAvailable(libuv)

if (WITH_LIBUV)
    add_executable(echo_libuv src/echo_tcp/libuv_server.cpp)
    target_include_directories(echo_libuv PRIVATE ${libuv_SOURCE_DIR}/include)
    if (TARGET uv_a)
        target_link_libraries(echo_libuv PRIVATE uv_a pthread)
    else()
        target_link_libraries(echo_libuv PRIVATE uv pthread)
    endif()
    if (ENABLE_LTO)
        include(CheckIPOSupported)
        check_ipo_supported(RESULT _ipo)
        if (_ipo)
            set_property(TARGET echo_libuv PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
        endif()
    endif()
endif()
