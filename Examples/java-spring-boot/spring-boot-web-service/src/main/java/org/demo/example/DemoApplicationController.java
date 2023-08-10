// SPDX-License-Identifier: BSD-3-Clause
// Copyright (C) 2023 Intel Corp.
//                          Bartłomiej Garbacz <bartomiej.garbacz@intel.com>
package org.demo.example;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class DemoApplicationController {

    @GetMapping("/")
    public String getString() {
        return "Hello from Graminized Spring Boot Application.\n";
    }
}
