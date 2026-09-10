import re

with open('src/pages/OverviewDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

import_block = '''import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';
'''
content = content.replace(\"import { InvestigationCase, CaseDetails } from '../types';\", \"import { InvestigationCase, CaseDetails } from '../types';\n\" + import_block)

charts_code = '''
      {/* 2. Intelligence Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1rem' }}>
        <div style={panelContainerStyle}>
          <h3 style={{ fontSize: '0.90rem', fontWeight: 700, color: '#f8fafc', marginBottom: '1rem' }}>Investigation Throughput (YTD)</h3>
          <div style={{ height: '220px', width: '100%' }}>
            <ResponsiveContainer width=\"100%\" height=\"100%\">
              <AreaChart data={[
                { month: 'Jan', investigations: 4, attribution_success: 3 },
                { month: 'Feb', investigations: 6, attribution_success: 5 },
                { month: 'Mar', investigations: 3, attribution_success: 3 },
                { month: 'Apr', investigations: 8, attribution_success: 6 },
                { month: 'May', investigations: 5, attribution_success: 4 },
                { month: 'Jun', investigations: Math.max(7, cases.length), attribution_success: completedCount }
              ]} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id=\"colorInv\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">
                    <stop offset=\"5%\" stopColor=\"#38bdf8\" stopOpacity={0.3}/>
                    <stop offset=\"95%\" stopColor=\"#38bdf8\" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id=\"colorSucc\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">
                    <stop offset=\"5%\" stopColor=\"#10b981\" stopOpacity={0.3}/>
                    <stop offset=\"95%\" stopColor=\"#10b981\" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray=\"3 3\" stroke=\"#334155\" vertical={false} />
                <XAxis dataKey=\"month\" stroke=\"#94a3b8\" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke=\"#94a3b8\" fontSize={12} tickLine={false} axisLine={false} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'var(--glass-panel)', border: '1px solid var(--glass-border)', borderRadius: '8px' }}
                  itemStyle={{ color: '#f8fafc', fontSize: '0.8rem' }}
                  labelStyle={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.25rem' }}
                />
                <Area type=\"monotone\" dataKey=\"investigations\" name=\"Total Cases\" stroke=\"#38bdf8\" fillOpacity={1} fill=\"url(#colorInv)\" />
                <Area type=\"monotone\" dataKey=\"attribution_success\" name=\"Attributed\" stroke=\"#10b981\" fillOpacity={1} fill=\"url(#colorSucc)\" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div style={panelContainerStyle}>
          <h3 style={{ fontSize: '0.90rem', fontWeight: 700, color: '#f8fafc', marginBottom: '1rem' }}>Global Risk Classifications</h3>
          <div style={{ height: '220px', width: '100%' }}>
            <ResponsiveContainer width=\"100%\" height=\"100%\">
              <BarChart data={[
                { level: 'CRITICAL', count: 2, fill: '#ef4444' },
                { level: 'HIGH', count: 5, fill: '#f97316' },
                { level: 'ELEVATED', count: 8, fill: '#f59e0b' },
                { level: 'LOW', count: 14, fill: '#10b981' },
              ]} margin={{ top: 10, right: 10, left: -20, bottom: 0 }} layout=\"vertical\">
                <CartesianGrid strokeDasharray=\"3 3\" stroke=\"#334155\" horizontal={false} />
                <XAxis type=\"number\" stroke=\"#94a3b8\" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis dataKey=\"level\" type=\"category\" stroke=\"#94a3b8\" fontSize={11} tickLine={false} axisLine={false} width={80} />
                <RechartsTooltip 
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{ backgroundColor: 'var(--glass-panel)', border: '1px solid var(--glass-border)', borderRadius: '8px' }}
                />
                <Bar dataKey=\"count\" name=\"Incidents\" radius={[0, 4, 4, 0]}>
                  {
                    [
                      { level: 'CRITICAL', count: 2, fill: '#ef4444' },
                      { level: 'HIGH', count: 5, fill: '#f97316' },
                      { level: 'ELEVATED', count: 8, fill: '#f59e0b' },
                      { level: 'LOW', count: 14, fill: '#10b981' },
                    ].map((entry, index) => (
                      <Cell key={\cell-\\} fill={entry.fill} />
                    ))
                  }
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
'''

content = content.replace('{/* 2. Main Split Content */}', charts_code + '\n\n      {/* 3. Main Split Content */}')

with open('src/pages/OverviewDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
