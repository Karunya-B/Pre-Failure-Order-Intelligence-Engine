risk_agent.py:
1.  we get data from data_store
2.  Then we do feature mappings/feature encoding-convert real world things to numbers 
    feature mapping= transforming input data into a new "feature space" where it is easier for an algorithm to process, classify, or analyze.
    we did numbering for each product based on relative importance//initially humans choose numbers and later ML learns from data
3.  _delay_factor - used to calculate risk
    min(1.0, (days - expected) / 3)-convert delay into a number between 0 and 1
    3+ day delay will cause 1 which is high risk
4.  _issue -calculates the delay for the order and also cancellation risk
5.  confidence_for_order-if not product we keep confidence as zero
                         we increase according to match type 
    this is similar to rule based uncertainity estimation-if data is unreliable it reduces confidence so we dont use NN here we do tradional ai method here
6.  stimulate_future_risk-look ahead logic 
                          if risk is bad rn how bad could it get soon
                          future risk = current risk + small uncertainty margin
                          we added risk on inventory status thats low ,
                          customer history is complainant and baby formula as product

7. build_risk_factors-you pass the values from the api request(you do that internally)
                      gap:customer_risk → derived from simple mapping (e.g., new, frequent_buyer)
                          product_delay_rate → derived from default category values  
                    factors:is the list of factors why the order is risk
                    impact:how much this factor contributes to the risk score
                    factors=[product_factor,delay_days,customer_risk,customer_sensitivity,customer_risk",future_risk_projection,inventory_status,category_delay_history]
