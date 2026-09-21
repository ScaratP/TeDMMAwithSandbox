package com.example.keelungsights.repository;

import com.example.keelungsights.model.Sight;
import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface SightRepository extends MongoRepository<Sight, String> {
    List<Sight> findByZone(String zone);
    boolean existsBySightName(String sightName); // 用於防止重複寫入
}