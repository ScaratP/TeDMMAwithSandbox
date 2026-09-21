package com.example.keelungsights.controller;

import com.example.keelungsights.model.Sight;
import com.example.keelungsights.service.SightService;

import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/sights")
public class SightController {
    private final SightService sightService;

    public SightController(SightService sightService) {
        this.sightService = sightService;
    }

    @GetMapping("/{zone}")
    public List<Sight> getSightsByZone(@PathVariable String zone) {
        return sightService.getSightsByZone(mapZone(zone)); // 呼叫 Service
    }

    private String mapZone(String zoneId) {
        return switch (zoneId.toLowerCase()) {
            case "zhongshan" -> "中山區";
            case "xinyi" -> "信義區";
            case "renai" -> "仁愛區";
            case "zhongzheng" -> "中正區";
            case "anle" -> "安樂區";
            case "qidu" -> "七堵區";
            case "nuannuan" -> "暖暖區";
            default -> zoneId;
        };
    }
}