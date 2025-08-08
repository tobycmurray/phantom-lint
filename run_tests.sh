#!/bin/bash

GOOD_TESTS=$(ls tests/good/*.{html,pdf})
BAD_TESTS=$(ls tests/bad/*.{html,pdf})

NUM_GOOD_TESTS=$(echo $(ls tests/good/*.{html,pdf} | wc -l))
NUM_BAD_TESTS=$(echo $(ls tests/bad/*.{html,pdf} | wc -l))

FAILED_TESTS=failed_tests.txt

echo > $FAILED_TESTS

let num_failed_tests=0
let num_passed_tests=0
let count=0
for i in ${GOOD_TESTS}; do
    base=$(basename $i)
    output_dir=output-good-$base
    output_file="${output_dir}/hidden_suspicious_phrases.txt"
    log_file="log-good-$base.txt"
    let count=$count+1
    echo -n "[$count/$NUM_GOOD_TESTS] "
    if [ ! -f "${output_file}" ]; then
	echo -n "Running good test $base...  "
	phantomlint "$i" --output "${output_dir}" --verbose --log-file "${log_file}" >tee-good-$base 2>&1
    else
	echo -n "Good test $base already run."
    fi
    # compute elapsed time
    start=$(head -1 "${log_file}" | cut -d' ' -f1)
    end=$(tail -1 "${log_file}" | cut -d' ' -f1)
    start_sec=$(date -j -f "%H:%M:%S" "$start" +%s)
    end_sec=$(date -j -f "%H:%M:%S" "$end" +%s)
    elapsed=$((end_sec - start_sec))
    
    hidden=$(cat "${output_file}")
    if [ ! -z "${hidden}" ]; then
	echo -n " FAILED"
	echo $i >> $FAILED_TESTS
	let num_failed_tests=$num_failed_tests+1
    else
	echo -n " OK   "
	let num_passed_tests=$num_passed_tests+1	
    fi
    echo " (${elapsed} seconds)"
done

let count=0
for i in ${BAD_TESTS}; do
    base=$(basename $i)
    output_dir=output-bad-$base
    output_file="${output_dir}/hidden_suspicious_phrases.txt"
    log_file="log-bad-$base.txt"
    let count=$count+1
    echo -n "[$count/$NUM_BAD_TESTS] "
    if [ ! -f "${output_file}" ]; then
	echo -n "Running bad test $base...  "
	phantomlint "$i" --output "${output_dir}" --verbose --log-file "${log_file}"  >tee-bad-$base 2>&1
    else
	echo -n "Bad test $base already run."
    fi
    # compute elapsed time
    start=$(head -1 "${log_file}" | cut -d' ' -f1)
    end=$(tail -1 "${log_file}" | cut -d' ' -f1)
    start_sec=$(date -j -f "%H:%M:%S" "$start" +%s)
    end_sec=$(date -j -f "%H:%M:%S" "$end" +%s)
    elapsed=$((end_sec - start_sec))
    
    hidden=$(cat "${output_file}")
    if [ -z "${hidden}" ]; then
	echo -n " FAILED"
	echo $i >> $FAILED_TESTS
	let num_failed_tests=$num_failed_tests+1	
    else
	echo -n " OK    "
	let num_passed_tests=$num_passed_tests+1	
    fi
    echo " (${elapsed} seconds)"    
done

echo "All tests done"

echo "Number of successful tests: $num_passed_tests"
echo "Number of failed tests:     $num_failed_tests"


    
