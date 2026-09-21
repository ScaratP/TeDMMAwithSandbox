package com.example.keelungsights.crawler;

import com.example.keelungsights.model.Sight;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Component
public class KeelungSightsCrawler {
    private static final String BASE_URL = "https://okgo.tw/buty/keelung.html";
    private static final String DOMAIN = "https://okgo.tw";
    private static final String USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

    public List<Sight> getItems(String zone) {
        List<Sight> sights = new ArrayList<>();
        try {
            Document doc = Jsoup.connect(BASE_URL).userAgent(USER_AGENT).timeout(10000).get();
            Elements h2s = doc.select("div.sec2 h2");
            Element zoneH2 = null;
            for (Element h2 : h2s) {
                if (h2.text().contains(zone)) {
                    zoneH2 = h2;
                    break;
                }
            }

            Set<String> detailUrls = new HashSet<>();
            if (zoneH2 != null) {
                Element secDiv = zoneH2.closest("div.sec2");
                if (secDiv != null) {
                    Elements aTags = secDiv.select("ul.dot li > a");
                    for (Element a : aTags) {
                        String href = a.attr("href");
                        if (href.contains("butyview.html")) {
                            String cleanHref = href.replace("../", "/");
                            detailUrls.add(cleanHref.startsWith("http") ? cleanHref : DOMAIN + cleanHref);
                        }
                    }
                }
            }

            for (String url : detailUrls) {
                Thread.sleep(1000);
                Document detailDoc = Jsoup.connect(url).userAgent(USER_AGENT).timeout(10000).get();
                Element sec3Div = detailDoc.selectFirst("div.sec3");

                String sightName = "";
                String address = zone + " ";
                String description = "";
                String photoURL = "https://via.placeholder.com/400x300?text=No+Image";

                if (sec3Div != null) {
                    // 1. 優先抓取圖片 (必須在刪除干擾節點前執行)
                    Element picDiv = sec3Div.selectFirst("div#Buty_Title_Pic img");
                    if (picDiv != null) {
                        String src = picDiv.attr("src");
                        if (src.startsWith("//"))
                            photoURL = "https:" + src;
                        else if (!src.startsWith("http"))
                            photoURL = DOMAIN + src;
                        else
                            photoURL = src;
                    }

                    // 2. 殺除不需要的網頁元件 (字級按鈕、圖片原始區塊、FB外掛程式碼)
                    sec3Div.select("#FontSize, #Buty_View_PicSource, script, style").remove();

                    // 3. 抓取景點名稱
                    Element h2 = sec3Div.selectFirst("h2");
                    if (h2 != null)
                        sightName = h2.text().trim();

                    // 4. 精準擷取地址 (利用塞入自訂符號來替代 <br> 進行切割)
                    sec3Div.select("br").after("===LINE===");
                    String[] lines = sec3Div.text().split("===LINE===");
                    for (String line : lines) {
                        String trimLine = line.trim();
                        if (trimLine.contains("地址：")) {
                            address = trimLine.substring(trimLine.indexOf("地址：") + 3).trim();
                        } else if (trimLine.contains("地址:")) {
                            address = trimLine.substring(trimLine.indexOf("地址:") + 3).trim();
                        }
                    }

                    // 5. 抓取描述 (抓取乾淨後的最長段落，並排除來源文字)
                    Elements pTags = sec3Div.select("p, div");
                    for (Element p : pTags) {
                        String text = p.text().trim();
                        if (text.length() > 30 && !text.contains("文章來源") && !text.contains("玩全台灣")) {
                            if (text.length() > description.length()) {
                                description = text.replace("===LINE===", "").trim();
                            }
                        }
                    }
                }

                // if (description.length() > 200)
                //     description = description.substring(0, 200) + "...";

                Sight sight = new Sight();
                sight.setSightName(sightName);
                sight.setZone(zone);
                sight.setCategory("");
                sight.setPhotoURL(photoURL);
                sight.setDescription(description);
                sight.setAddress(address);
                sights.add(sight);
            }
        } catch (Exception e) {
            System.out.println("爬取 " + zone + " 時發生異常：" + e.getMessage());
        }

        if (sights.isEmpty()) {
            System.out.println("查無 " + zone + " 真實景點，建立 Demo 測試資料");
            Sight demoSight = new Sight();
            demoSight.setSightName(zone + "測試景點");
            demoSight.setZone(zone);
            demoSight.setCategory("");
            demoSight.setPhotoURL("https://via.placeholder.com/400x300?text=Demo+Sight");
            demoSight.setDescription("這是 " + zone + " 的測試景點描述，因為原網站缺乏此區資料。");
            demoSight.setAddress("基隆市" + zone + "測試路1號");
            sights.add(demoSight);
        }

        return sights;
    }

    public static void main(String[] args) {
        KeelungSightsCrawler crawler = new KeelungSightsCrawler();
        Sight[] sights = crawler.getItems("qidu").toArray(new Sight[0]);
        for (Sight s : sights) {
            System.out.println(s);
        }
    }
}
