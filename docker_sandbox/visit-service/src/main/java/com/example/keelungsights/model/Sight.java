package com.example.keelungsights.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import lombok.Data;

@Data // 若沒用 Lombok，請自行補上 getter 和 setter
@Document(collection = "sights")
public class Sight {
    @Id
    private String id;
    private String sightName;
    private String zone;
    private String category;
    private String photoURL;
    private String description;
    private String address;
}