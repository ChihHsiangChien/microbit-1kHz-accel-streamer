project(codal-core C CXX)

# --- 手動設定版本資訊，避免 Git 報錯 ---
set( CODAL_VERSION_MAJOR  0 )
set( CODAL_VERSION_MINOR  1 )
set( CODAL_VERSION_PATCH  0 )
set( CODAL_VERSION_HASH   "manual" )

# 註解掉原本的 Git 抓取邏輯，防止在無 Git 環境下出錯
# execute_process( WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../${codal.target.name}" COMMAND git describe --tags --abbrev=0 OUTPUT_VARIABLE git_tag_string )
# execute_process( WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../${codal.target.name}" COMMAND "git" "log" "--pretty=format:%h" "-n" "1" OUTPUT_VARIABLE CODAL_VERSION_HASH )
# string( REGEX MATCHALL "[0-9]+" git_tag "${git_tag_string}" )

# 由於已經手動賦值，不再需要 list 操作
# list(LENGTH git_tag len)
# if( ${len} GREATER 0 )
#     list(GET git_tag 0 CODAL_VERSION_MAJOR )
#     list(GET git_tag 1 CODAL_VERSION_MINOR )
#     list(GET git_tag 2 CODAL_VERSION_PATCH )
# endif()
# --------------------------------------

# 產生版本標頭檔 (這行必須保留)
configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/inc/core/codal_version.h.in" "${CMAKE_CURRENT_BINARY_DIR}/gen/codal_version.h" )

# 尋找原始碼與標頭檔
RECURSIVE_FIND_DIR(INCLUDE_DIRS "./inc" "*.h")
RECURSIVE_FIND_FILE(SOURCE_FILES "./source" "*.c??")

# 建立函式庫
add_library(codal-core
    ${SOURCE_FILES}
)

# 設定引用路徑
target_include_directories(codal-core PUBLIC ${INCLUDE_DIRS} "${CMAKE_CURRENT_BINARY_DIR}/gen/" )
