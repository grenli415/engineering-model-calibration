# Calibration report

Provenance: synthetic: power-law baseline with known corrections and 1% Gaussian noise

Independent split labels were provided by the data author. Only train rows entered fitting.

```
     split     model  n      mae     rmse  mape_pct  max_abs_error  zero_reference_count
     train   thermal 90 0.451568 0.688474  0.784400       2.931548                     0
     train hydraulic 90 0.006482 0.008438  0.747795       0.022697                     0
validation   thermal 30 0.406767 0.588850  0.726705       1.948458                     0
validation hydraulic 30 0.006563 0.008072  0.730204       0.020354                     0
```

Rows outside training Re/temperature rectangle: 0.

![Comparison and residuals](comparison.png)

See range_metrics.csv for Reynolds and temperature bands. Synthetic recovery is an algorithm test, not experimental or manufacturer validation. Repeated conditions/specimens must be grouped before splitting. The fit does not estimate measurement uncertainty or establish safety margins.
