package com.example.keelungsights.service;

import com.example.keelungsights.model.Sight;
import com.example.keelungsights.repository.SightRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SightService {
    private final SightRepository repository;

    public SightService(SightRepository repository) {
        this.repository = repository;
    }

    public List<Sight> getSightsByZone(String zone) {
        return repository.findByZone(zone);
    }
}