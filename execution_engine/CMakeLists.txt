cmake_minimum_required(VERSION 3.16)
project(JockeyEngine VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

option(BUILD_SHARED "Build shared lib (dev/test only)" OFF)
option(HARDEN "Production hardening flags" ON)

if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -Wno-unused-parameter -Wno-cast-function-type -Wno-pedantic")
    set(CMAKE_C_FLAGS_RELEASE "-O2 -DNDEBUG -DENABLE_LOGGING=1 -g0")
    set(CMAKE_C_FLAGS_DEBUG   "-g -O0 -DDEBUG -DENABLE_LOGGING=1")
elseif(MSVC)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /W3 /O2 /MP")
endif()

if(HARDEN AND CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(
        -fvisibility=hidden              # hide non-public symbols
        -fno-stack-protector             # no libssp dependency
        -fno-asynchronous-unwind-tables  # no libgcc unwind refs
        -fno-unwind-tables
        -ffunction-sections
        -fdata-sections
        -fno-ident
        -fPIC
    )
    add_link_options(
        -Wl,--gc-sections                # drop unused code
        -static-libgcc                   # no libgcc_s_seh-1.dll
        -static-libstdc++
    )
    # Deterministic builds ? strip source paths from debug info
    add_compile_options(-ffile-prefix-map=${CMAKE_SOURCE_DIR}=.)
    add_compile_options(-ffile-prefix-map=${CMAKE_BINARY_DIR}=.)
endif()

include_directories(${CMAKE_SOURCE_DIR}/include)

set(COMMON_SOURCES
    src/api_unhooking.c
    src/byovd_loader.c
    src/inject.c
    src/other_injections.c
    src/process_hollowing.c
    src/reflective_dll.c
)

if(WIN32)
    list(APPEND COMMON_SOURCES src/pal/pal_win.c src/syscalls/syscalls_win.c)
    set(PLATFORM_LIBS psapi setupapi advapi32)
    add_definitions(-D_WIN32_WINNT=0x0A00 -DWIN32_LEAN_AND_MEAN -D_WIN64)
else()
    list(APPEND COMMON_SOURCES src/pal/pal_linux.c src/syscalls/syscalls_linux.c)
    set(PLATFORM_LIBS dl pthread)
    add_definitions(-D_GNU_SOURCE)
endif()

# ---- Static library: production target ----
add_library(jockey STATIC ${COMMON_SOURCES})
target_link_libraries(jockey ${PLATFORM_LIBS})
set_target_properties(jockey PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    OUTPUT_NAME jockey
)

# ---- Shared library: dev/test only ----
if(BUILD_SHARED)
    add_library(jockey_shared SHARED ${COMMON_SOURCES})
    set_target_properties(jockey_shared PROPERTIES OUTPUT_NAME jockey POSITION_INDEPENDENT_CODE ON)
    target_link_libraries(jockey_shared ${PLATFORM_LIBS})
endif()

# ---- Demo: dev only ----
if(BUILD_SHARED OR CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_executable(jockey_demo demo/main.c)
    target_link_libraries(jockey_demo jockey ${PLATFORM_LIBS})
endif()

message(STATUS "Proteus- Execution Engine")
message(STATUS "  Platform:    ${CMAKE_SYSTEM_NAME}")
message(STATUS "  Compiler:    ${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}")
message(STATUS "  Build type:  ${CMAKE_BUILD_TYPE}")
message(STATUS "  Shared lib:  ${BUILD_SHARED}")
message(STATUS "  Hardened:    ${HARDEN}")
