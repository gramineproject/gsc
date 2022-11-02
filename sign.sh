#!/usr/bin/expect
spawn gramine-sgx-sign \
      --keytype [lindex $argv 0] \
      --key [lindex $argv 1] \
      --manifest [lindex $argv 2] \
      --output [lindex $argv 3]

set timeout -1
set times 0
set maxtimes 1
expect "Enter pass phrase for [lindex $argv 0]" {
    if {$times > $maxtimes} {
        exit 0
    }
    send "[lindex $argv 4]\r"
    set times [ expr $times + 1];
    exp_continue
}
