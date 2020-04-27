#!/bin/bash

function foo() {

    echo "foo return 1"
    return 1
}

echo "start"
foo
echo "status $?"