#!/bin/bash

GOOD_TESTS=$(ls tests/good/*.{pdf,html})
BAD_TESTS=$(ls tests/bad/*.{pdf,html})

FAILED_TESTS=failed_tests.txt

echo > $FAILED_TESTS

let num_failed_tests=0
let num_passed_tests=0
for i in ${GOOD_TESTS}; do
    base=$(basename $i)
    output_dir=output-good-$base
    output_file="${output_dir}/hidden_suspicious_phrases.txt"
    if [ ! -f "${output_file}" ]; then
	echo "Running good test $base..."
	phantomlint $i --output ${output_dir} --verbose --log-file log-good-$base.txt >tee-good-$base 2>&1
    else
	echo "Good test $base already run. Skipping"
    fi
    hidden=$(cat "${output_file}")
    if [ ! -z "${hidden}" ]; then
	echo "Good test $base failed"
	echo $i >> $FAILED_TESTS
	let num_failed_tests=$num_failed_tests+1
    else
	let num_passed_tests=$num_passed_tests+1	
    fi
done


for i in ${BAD_TESTS}; do
    base=$(basename $i)
    output_dir=output-bad-$base
    output_file="${output_dir}/hidden_suspicious_phrases.txt"
    if [ ! -f "${output_file}" ]; then
	echo "Running bad test $base..."
	phantomlint $i --output ${output_dir} --verbose --log-file log-bad-$base.txt >tee-bad-$base 2>&1
    else
	echo "Bad test $base already run. Skipping"
    fi
    hidden=$(cat "${output_file}")
    if [ -z "${hidden}" ]; then
	echo "Bad test $base failed"
	echo $i >> $FAILED_TESTS
	let num_failed_tests=$num_failed_tests+1	
    else
	let num_passed_tests=$num_passed_tests+1	
    fi
done

echo "All tests done"

echo "Number of successful tests: $num_passed_tests"
echo "Number of failed tests:     $num_failed_tests"


    
