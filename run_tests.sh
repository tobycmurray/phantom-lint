#!/usr/bin/env bash
set -euo pipefail
set -x

# Default mode
QUICK_MODE=false

# Check for -quick flag
if [[ "${1:-}" == "-quick" ]]; then
    QUICK_MODE=true
    echo "Running in quick mode..."
    shift  # remove the flag so $@ contains only test arguments, if any
fi

# clear failed tests log
FAILED_TESTS=$(mktemp /tmp/failed_tests.XXXXXX)
echo -n > $FAILED_TESTS

# directory where all test output is placed
TESTS_OUTPUT=$(mktemp -d /tmp/tests_output.XXXXXX)
mkdir -p "${TESTS_OUTPUT}"

echo "All test output will be placed in: ${TESTS_OUTPUT}"

# needed for the TESTS=... variable-expansion and glob stuff to work below
shopt -s nullglob

num_failed_tests=0
num_passed_tests=0

for kind in good bad; do
    if [ "$QUICK_MODE" = true ]; then
	TESTS=(tests/"$kind"/fake_*.{html,pdf})  # tests is an array
    else
	TESTS=(tests/"$kind"/*.{html,pdf})  # tests is an array
    fi
    NUM_TESTS=${#TESTS[@]}
    echo "Running ${NUM_TESTS} ${kind} tests..."
    count=0
    for i in "${TESTS[@]}"; do
	base=$(basename $i)
	output_dir="${TESTS_OUTPUT}/output-$kind-$base"
	output_file="${output_dir}/hidden_suspicious_phrases.txt"
	log_file="${TESTS_OUTPUT}/log-${kind}-$base.txt"
	let count=$count+1
	msg="  [$count/$NUM_TESTS]"
	if [ ! -f "${output_file}" ]; then
	    msg="$msg Running ${kind} test $base..."
	    phantomlint "$i" --output "${output_dir}" --verbose --log-file "${log_file}" >"${TESTS_OUTPUT}/tee-${kind}-$base" 2>&1
	    echo -n "$msg"
	else
	    msg="$msg ${kind} test $base already run."
	    echo -n "$msg"
	fi
	# compute elapsed time
	start=$(head -1 "${log_file}" | cut -d' ' -f1)
	end=$(tail -1 "${log_file}" | cut -d' ' -f1)
	IFS=: read -r h m s <<< "$start"
	start_sec=$((10#$h*3600 + 10#$m*60 + 10#$s))	
	IFS=: read -r h m s <<< "$end"
	end_sec=$((10#$h*3600 + 10#$m*60 + 10#$s))	
	elapsed=$((end_sec - start_sec))
    
	hidden=$(cat "${output_file}")
	FAILED=0
	if [ ! -z "${hidden}" ]; then
	    # hidden phrases detected
	    if [ "$kind" = "good" ]; then
		FAILED=1
	    fi
	else
	    # nothing hidden detected
	    if [ "$kind" = "bad" ]; then
		FAILED=1
	    fi
	fi

	msg_len=${#msg}  # get length of stuff already printed out
	RES="    OK"
	if [ "$FAILED" -ne 0 ]; then
	    echo $i >> $FAILED_TESTS
	    let num_failed_tests=$num_failed_tests+1
	    RES="FAILED"
	else
	    let num_passed_tests=$num_passed_tests+1	    
	fi
	str="$RES ($elapsed secs)"
	cols=${COLUMNS:-80}
	avail=$(( cols - msg_len ))
	printf "%*s\n" "$avail" "$str"
    done
done


echo "All tests done"

echo "Number of successful tests: $num_passed_tests"
echo "Number of failed tests:     $num_failed_tests"

if [ "$num_failed_tests" -ne 0 ]; then
    echo "Failed tests are listed in ${FAILED_TESTS}"
    exit 1
fi

# success
exit 0
