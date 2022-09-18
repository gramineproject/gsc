#!/usr/bin/expect
spawn gramine-sgx-sign \
      --key [lindex $argv 0] \
      --manifest [lindex $argv 1] \
      --output [lindex $argv 2]

set timeout -1
set times 0
set maxtimes 1
expect "Enter pass phrase for [lindex $argv 0]" {
    if {$times > $maxtimes} {
        exit 0
    }
    send "[lindex $argv 3]\r"
    set times [ expr $times + 1];
    exp_continue
}
