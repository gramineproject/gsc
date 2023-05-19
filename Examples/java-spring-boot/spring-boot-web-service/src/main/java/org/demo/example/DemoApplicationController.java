// SPDX-License-Identifier: LGPL-3.0-or-later
// Copyright (C) 2023 Intel Corporation
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
