package com.example.keelungsights.config;

import com.example.keelungsights.crawler.KeelungSightsCrawler;
import com.example.keelungsights.model.Sight;
import com.example.keelungsights.repository.SightRepository;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class DataInitRunner implements ApplicationRunner {
    private final SightRepository repository;
    private final KeelungSightsCrawler crawler;
    private static final String[] ZONES = {"中山區", "信義區", "仁愛區", "中正區", "安樂區", "七堵區", "暖暖區"};

    public DataInitRunner(SightRepository repository, KeelungSightsCrawler crawler) {
        this.repository = repository;
        this.crawler = crawler;
    }

    @Override
    public void run(ApplicationArguments args) throws Exception {
        if (repository.count() == 0) {
            System.out.println("資料庫為空，啟動 Jsoup 爬蟲初始化資料...");
            for (String zone : ZONES) {
                List<Sight> sights = crawler.getItems(zone);

                System.out.println(zone + " 抓取到 " + sights.size() + " 筆景點");
                
                for (Sight sight : sights) {
                    if (!repository.existsBySightName(sight.getSightName())) {
                        repository.save(sight);
                    }
                }
            }
            System.out.println("✅ MongoDB 初始化完成！");
        }
    }
}