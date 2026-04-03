cmake_minimum_required(VERSION 3.6)

# include additional cmake
include(utils/cmake/JSONParser.cmake)
include(utils/cmake/util.cmake)
include(utils/cmake/colours.cmake)

if (NOT "${BUILD_TOOL}" STRGREATER "")
    set(BUILD_TOOL "CODAL")
endif()

#
# Supress unecessary (and often inaccurate) validity check of the toolchain
#
set(CMAKE_C_COMPILER_WORKS 1)
set(CMAKE_CXX_COMPILER_WORKS 1)


#read our config file...
file(READ "./codal.json" codal_json_str)
sbeParseJson(codal codal_json_str)

set(CODAL_APP_OUTPUT_DIR ".")
set(CODAL_APP_SOURCE_DIR "source")

if("${codal.application}" STRGREATER "")
    set(CODAL_APP_SOURCE_DIR "${codal.application}")
endif()

if("${codal.output_folder}" STRGREATER "")
    set(CODAL_APP_OUTPUT_DIR "${codal.output_folder}")
endif()

if(NOT "${codal.target.name}" STRGREATER "")
    message(FATAL_ERROR "${BoldRed}INVALID TARGET.${ColourReset}")
endif()

set(CODAL_DEPS "")
set(LIB_DEST "libraries")

# Use target-locked.json from the library if it exists, otherwise target.json
if(EXISTS "./${LIB_DEST}/${codal.target.name}/target-locked.json")
    file(READ "./${LIB_DEST}/${codal.target.name}/target-locked.json" device_json_str)
    message("${BoldMagenta}Using target-locked.json${ColourReset}")
else()
    file(READ "./${LIB_DEST}/${codal.target.name}/target.json" device_json_str)
    message("${BoldMagenta}Using target.json${ColourReset}")
endif()

message("${BoldBlue}Targeting ${codal.target.name}${ColourReset}")

sbeParseJson(device device_json_str)

SET(CODAL_TARGET_NAME ${device.target.name})
SET(CODAL_OUTPUT_NAME ${device.device})
SET(CODAL_TARGET_PROCESSOR ${device.processor})
SET(CODAL_TARGET_CPU_ARCHITECTURE ${device.architecture})

####################

SET(TOOLCHAIN ${device.toolchain})
SET(TOOLCHAIN_FOLDER "./utils/cmake/toolchains/${device.toolchain}")

# include toolchain file
set(CMAKE_TOOLCHAIN_FILE "${TOOLCHAIN_FOLDER}/toolchain.cmake" CACHE PATH "toolchain file")

# required to force TOOLCHAIN settings...
project(${device.device})
enable_language(ASM)

# include compiler flags overrides
include(${TOOLCHAIN_FOLDER}/compiler-flags.cmake)
set(PLATFORM_INCLUDES_PATH "${PROJECT_SOURCE_DIR}/utils/cmake/toolchains/${device.toolchain}")

file(MAKE_DIRECTORY "${PROJECT_SOURCE_DIR}/build")

# configure output directories
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY  "${PROJECT_SOURCE_DIR}/build")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/build")

SET(CODAL_DEFINITIONS "")

# apply cpu_opts
if("${device.cpu_opts}" STRGREATER "")
    set(CMAKE_ASM_FLAGS "${CMAKE_ASM_FLAGS} ${device.cpu_opts}")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${device.cpu_opts}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${device.cpu_opts}")
    set(CMAKE_LINKER_FLAGS "${CMAKE_LINKER_FLAGS} ${device.cpu_opts}")
endif()

# asm flags
if("${device.asm_flags}" STRGREATER "")
    set(CMAKE_ASM_FLAGS "${CMAKE_ASM_FLAGS} ${device.asm_flags}")
endif()

# c flags
if("${device.c_flags}" STRGREATER "")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${device.c_flags}")
endif()

# cpp flags
if("${device.cpp_flags}" STRGREATER "")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${device.cpp_flags}")
endif()

# linker flags
if("${device.linker_flags}" STRGREATER "")
    set(CMAKE_LINKER_FLAGS "${CMAKE_LINKER_FLAGS} ${device.linker_flags}")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${device.linker_flags}")
endif()

# extract configuration and create extra definitions header
EXTRACT_JSON_ARRAY(codal "codal\\.config\\." CODAL_FIELDS CODAL_VALUES)
EXTRACT_JSON_ARRAY(device "device\\.config\\." DEVICE_FIELDS DEVICE_VALUES)
UNIQUE_JSON_KEYS(CODAL_FIELDS CODAL_VALUES DEVICE_FIELDS DEVICE_VALUES FINAL_FIELDS FINAL_VALUES)
FORM_DEFINITIONS(FINAL_FIELDS FINAL_VALUES CODAL_DEFINITIONS)

if("${CODAL_DEFINITIONS}" STRGREATER "")
    set(EXTRA_INCLUDES_NEW_PATH "${PROJECT_SOURCE_DIR}/build/codal_extra_definitions_new.h")
    set(EXTRA_INCLUDES_PATH "${PROJECT_SOURCE_DIR}/build/codal_extra_definitions.h")
    file(WRITE "${EXTRA_INCLUDES_NEW_PATH}" "${CODAL_DEFINITIONS}")
    configure_file(${EXTRA_INCLUDES_NEW_PATH} ${EXTRA_INCLUDES_PATH} COPYONLY)

    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -include \"${EXTRA_INCLUDES_PATH}\"")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -include \"${EXTRA_INCLUDES_PATH}\"")
endif()

# define any additional symbols specified by the target.
if("${device.definitions}" STRGREATER "")
    add_definitions("${device.definitions}")
endif()

# Hybrid Mode Overrides
add_definitions(-DSOFTDEVICE_PRESENT=1 -DS113)
add_definitions(-DNRF_SDH_BLE_GATT_MAX_MTU_SIZE=247)
add_definitions(-DNRF_SDH_BLE_GAP_DATA_LENGTH=251)
add_definitions(-DNRF_SDH_BLE_GATTS_ATTR_TAB_SIZE=1600)

# Add platform includes
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -I\"${PLATFORM_INCLUDES_PATH}\"")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -I\"${PLATFORM_INCLUDES_PATH}\"")

# Include the root of the libraries folder
include_directories("${PROJECT_SOURCE_DIR}/${LIB_DEST}")

# Include nrfx paths
include_directories("${PROJECT_SOURCE_DIR}/libraries/codal-nrf52/inc")
include_directories("${PROJECT_SOURCE_DIR}/libraries/codal-nrf52/nrfx")
include_directories("${PROJECT_SOURCE_DIR}/libraries/codal-nrf52/nrfx/drivers/include")
include_directories("${PROJECT_SOURCE_DIR}/libraries/codal-nrf52/nrfx/hal")
include_directories("${PROJECT_SOURCE_DIR}/libraries/codal-nrf52/nrfx/mdk")
include_directories("${PROJECT_SOURCE_DIR}/libraries/codal-nrf52/inc/cmsis")
include_directories("${PROJECT_SOURCE_DIR}/libraries/codal-nrf52/nrfx/templates")

# Libraries
set(CODAL_DEPS "codal-microbit-v2;codal-nrf52;codal-core;codal-microbit-nrf5sdk")

foreach(dep ${CODAL_DEPS})
    add_subdirectory("${PROJECT_SOURCE_DIR}/${LIB_DEST}/${dep}")
endforeach()

#finally, find sources and includes of the application, and create a target.
RECURSIVE_FIND_DIR(INCLUDE_DIRS "${PROJECT_SOURCE_DIR}/${CODAL_APP_SOURCE_DIR}" "*.h")
RECURSIVE_FIND_FILE(SOURCE_FILES "${PROJECT_SOURCE_DIR}/${CODAL_APP_SOURCE_DIR}" "*.cpp")

if("${SOURCE_FILES}" STREQUAL "")
    message(FATAL_ERROR "${BoldRed}No user application to build, please add a main.cpp at: ${PROJECT_SOURCE_DIR}/${CODAL_APP_SOURCE_DIR}${ColourReset}")
endif()

add_executable(
    ${device.device}
    ${SOURCE_FILES}
)

target_include_directories(${device.device} PUBLIC "${INCLUDE_DIRS}")

target_link_libraries(
    ${device.device}
    codal-microbit-v2
    codal-nrf52
    codal-core
    codal-microbit-nrf5sdk
)

# Bin / Hex generation
include("${TOOLCHAIN_FOLDER}/bin-generator.cmake")
include("${TOOLCHAIN_FOLDER}/hex-generator.cmake")
include("${TOOLCHAIN_FOLDER}/size-info.cmake")
